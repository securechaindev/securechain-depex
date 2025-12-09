from typing import Any

from z3 import ArithRef, AstVector, Real, parse_smt2_string

from app.utils import VersionFilter


class SMTModel:
    def __init__(self, source_data: dict[str, Any], node_type: str, aggregator: str) -> None:
        self.source_data = source_data
        self.aggregator = aggregator
        self.node_type = node_type
        self.domain: AstVector | None = None
        self.func_obj: ArithRef | None = None
        self.impacts: set[str] = set()
        self.childs: dict[str, dict[str, set[int]]] = {}
        self.parents: dict[str, dict[str, set[int]]] = {}
        self.directs: list[str] = []
        self.var_domain: set[str] = set()
        self.indirect_vars: set[str] = set()
        self.ctc_domain: str = ""
        self.ctcs: dict[str, dict[float, set[int]]] = {}
        self.filtered_versions: dict[str, list[int]] = {}

    def convert(self, model_text: str) -> None:
        self.domain = parse_smt2_string(model_text)
        name = self.source_data.get('name', 'unknown')
        self.func_obj = Real(f"file_risk_{name}")

    def transform(self) -> str:
        for key in ["direct", "indirect"]:
            for require in self.source_data.get("require", {}).get(key, []):
                getattr(self, f"transform_{key}_package")(require)
        file_risk_name = f"file_risk_{self.source_data.get('name', 'unknown')}"
        self.var_domain.add(f"(declare-const {file_risk_name} Real)")
        self.build_indirect_constraints()
        self.build_impact_constraints()
        str_sum = self.build_impact_sum()
        self.ctc_domain += f"(= {file_risk_name} {str_sum})"
        for indirect_var in self.indirect_vars:
            self.var_domain.add(f"(declare-const |{indirect_var}| Int)")
            self.var_domain.add(f"(declare-const |impact_{indirect_var}| Real)")
        model_text = f"{' '.join(self.var_domain)} (assert (and {self.ctc_domain}))"
        self.domain = parse_smt2_string(model_text)
        self.func_obj = Real(file_risk_name)
        return model_text

    def transform_direct_package(self, require: dict[str, Any]) -> None:
        package = require.get("package", "")
        constraints = require.get("constraints", "")

        versions_impacts = self.get_filtered_versions_impacts(package, constraints)
        versions_names = list(versions_impacts.keys())

        self.directs.append(f"|{package}|")
        var_impact = f"|impact_{package}|"
        self.impacts.add(var_impact)
        self.var_domain.add(f"(declare-const |{package}| Int)")
        self.var_domain.add(f"(declare-const {var_impact} Real)")
        self.build_direct_constraint(package, versions_names)
        self.filtered_versions[package] = versions_names
        self.transform_versions(versions_impacts, package)

    def transform_indirect_package(self, require: dict[str, Any]) -> None:
        package = require.get("package", "")
        constraints = require.get("constraints", "")
        parent_version_name = require.get("parent_version_name", "")
        parent_serial_number = require.get("parent_serial_number", -1)

        versions_impacts = self.get_filtered_versions_impacts(package, constraints)
        versions_names = list(versions_impacts.keys())

        self.append_indirect_constraint(
            package,
            versions_names,
            parent_version_name,
            parent_serial_number,
        )
        self.filtered_versions[package] = versions_names
        self.transform_versions(versions_impacts, package, require)

    def get_filtered_versions_impacts(self, package: str, constraints: str) -> dict[int, int]:
        package_versions = self.source_data.get("have", {}).get(package, [])
        filtered_versions = VersionFilter.filter_versions(
            self.node_type,
            package_versions,
            constraints
        )
        return {
            version.get("serial_number", -1): version.get(self.aggregator, 0)
            for version in filtered_versions
        }

    def transform_versions(self, versions: dict[int, int], var: str, require: dict[str, Any] | None = None) -> None:
        parent_version_name = require.get("parent_version_name") if require else None
        parent_serial_number = require.get("parent_serial_number") if require else None

        if not require or (
            parent_version_name in self.filtered_versions and
            parent_serial_number in self.filtered_versions.get(parent_version_name, [])
        ):
            impact_version_group = {}
            if require:
                package = require.get('package', '')
                self.impacts.add(f"|impact_{package}|")
                self.indirect_vars.add(var)
                if parent_version_name:
                    self.indirect_vars.add(parent_version_name)
                impact_version_group = {0.0: {-1}}
            for version, impact in versions.items():
                self.ctcs.setdefault(var, impact_version_group).setdefault(impact, set()).add(version)

    def append_indirect_constraint(
        self, child: str, versions: list[int], parent: str, version: int
    ) -> None:
        if versions and parent in self.filtered_versions and version in self.filtered_versions.get(parent, []):
            self.childs.setdefault(
                self.group_versions(child, versions, False), {}
            ).setdefault(parent, set()).add(version)
            if child not in self.directs:
                self.parents.setdefault(child, {}).setdefault(parent, set()).add(
                    version
                )

    def build_direct_constraint(self, var: str, versions: list[int]) -> None:
        if versions:
            self.ctc_domain += f"{self.group_versions(var, versions, False)} "
        else:
            self.ctc_domain += "false "

    def build_indirect_constraints(self) -> None:
        for versions, _ in self.childs.items():
            for parent, parent_versions in _.items():
                self.ctc_domain += f"(=> {self.group_versions(parent, list(parent_versions), True)} {versions}) "
        for child, _ in self.parents.items():
            for parent, parent_versions in _.items():
                self.ctc_domain += f"(=> (not {self.group_versions(parent, list(parent_versions), True)}) (= |{child}| -1)) "

    def build_impact_constraints(self) -> None:
        for var, _ in self.ctcs.items():
            for impact, versions in _.items():
                self.ctc_domain += f"(=> {self.group_versions(var, list(versions), True)} (= |impact_{var}| {impact})) "

    def group_versions(
        self,
        var: str,
        versions: list[int],
        ascending: bool
    ) -> str:
        if not versions:
            return ""
        constraints: list[str] = []
        current_group = [versions[0]]
        step = 1 if ascending else -1
        for i in range(1, len(versions)):
            if versions[i] == versions[i - 1] + step:
                current_group.append(versions[i])
            else:
                constraints.append(self.create_constraint_for_group(f"|{var}|", current_group, ascending))
                current_group = [versions[i]]
        constraints.append(self.create_constraint_for_group(f"|{var}|", current_group, ascending))
        return constraints[0] if len(constraints) == 1 else f"(or {' '.join(constraints)})"

    @staticmethod
    def create_constraint_for_group(var: str, group: list[int], ascending: bool) -> str:
        if len(group) == 1:
            return f"(= {var} {group[0]})"
        min_val, max_val = (group[0], group[-1]) if ascending else (group[-1], group[0])
        return f"(and (>= {var} {min_val}) (<= {var} {max_val}))"

    def build_impact_sum(self) -> str:
        return f"(+ {' '.join(self.impacts)})" if self.impacts else "0.0"
