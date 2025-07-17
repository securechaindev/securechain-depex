from typing import Any

from univers.version_range import (
    CargoVersionRange,
    GemVersionRange,
    MavenVersionRange,
    NpmVersionRange,
    NugetVersionRange,
    PypiVersionRange,
    VersionRange,
)
from univers.versions import (
    MavenVersion,
    NugetVersion,
    PypiVersion,
    RubygemsVersion,
    SemverVersion,
    Version,
)
from z3 import ArithRef, BoolRef, Real, parse_smt2_string


class SMTModel:
    def __init__(
        self,
        source_data: dict[str, Any],
        node_type: str,
        agregator: str,
    ) -> None:
        self.source_data: dict[str, Any] = source_data
        self.agregator: str = agregator
        self.domain: BoolRef = None
        self.func_obj_var: ArithRef = None
        self.version_type, self.range_type = self.get_version_range_type(
            node_type
        )
        self.impacts: set[str] = set()
        self.childs: dict[str, dict[str, set[int]]] = {}
        self.parents: dict[str, dict[str, set[int]]] = {}
        self.directs: list[str] = []
        self.var_domain: set[str] = set()
        self.ctc_domain: str = ""
        self.ctcs: dict[str, dict[float, set[int]]] = {}
        self.filtered_versions: dict[str, dict[int, int]] = {}

    def convert(self, model_text: str) -> None:
        self.domain = parse_smt2_string(model_text)
        self.func_obj_var = Real(
            f"func_obj_{self.source_data["name"]}"
        )

    def transform(self) -> str:
        if "direct" in self.source_data["requires"]:
            for rel_requires in self.source_data["requires"]["direct"]:
                self.transform_direct_package(rel_requires)
        if "indirect" in self.source_data["requires"]:
            for rel_requires in self.source_data["requires"]["indirect"]:
                self.transform_indirect_package(rel_requires)
        func_obj_name = f"func_obj_{self.source_data["name"]}"
        file_risk_name = f"file_risk_{self.source_data["name"]}"
        self.var_domain.add(
            f"(declare-const {func_obj_name} Real) (declare-const {file_risk_name} Real)"
        )
        self.build_indirect_constraints()
        self.build_impact_constraints()
        str_sum = self.sum()
        self.ctc_domain += f"(= {file_risk_name} {self.agregate(str_sum)}) "
        self.ctc_domain += f"(= {func_obj_name} {self.mean(str_sum)})"
        model_text = f"{" ".join(self.var_domain)}(assert (and {self.ctc_domain}))"
        self.domain = parse_smt2_string(model_text)
        self.func_obj_var = Real(
            f"func_obj_{self.source_data["name"]}"
        )
        return model_text

    def transform_direct_package(self, rel_requires: dict[str, Any]) -> None:
        filtered_versions = self.filter_versions(
            rel_requires["dependency"], rel_requires["constraints"]
        )
        if filtered_versions:
            self.directs.append(rel_requires["dependency"])
            var_impact = f"impact_{rel_requires['dependency']}"
            self.impacts.add(var_impact)
            self.var_domain.add(f"(declare-const {rel_requires['dependency']} Int)")
            self.var_domain.add(f"(declare-const {var_impact} Real)")
            self.build_direct_contraint(
                rel_requires["dependency"], list(filtered_versions.keys())
            )
            self.transform_versions(filtered_versions, rel_requires["dependency"])

    def transform_indirect_package(self, rel_requires: dict[str, Any]) -> None:
        filtered_versions = self.filter_versions(
            rel_requires["dependency"], rel_requires["constraints"]
        )
        if filtered_versions:
            var_impact = f"impact_{rel_requires['dependency']}"
            self.impacts.add(var_impact)
            self.var_domain.add(f"(declare-const {rel_requires['dependency']} Int)")
            self.var_domain.add(f"(declare-const {var_impact} Real)")
            self.var_domain.add(
                f"(declare-const {rel_requires['parent_version_name']} Int)"
            )
            self.append_indirect_constraint(
                rel_requires["dependency"],
                list(filtered_versions.keys()),
                rel_requires["parent_version_name"],
                rel_requires["parent_count"],
            )
            self.transform_versions(filtered_versions, rel_requires["dependency"])

    def transform_versions(self, versions: dict[int, int], var: str) -> None:
        for version, impact in versions.items():
            self.ctcs.setdefault(var, {}).setdefault(impact, set()).add(version)

    def filter_versions(self, dependency: str, constraints: str) -> dict[int, int]:
        filtered_versions = self.filtered_versions.setdefault(
            f"{dependency}{constraints}", {}
        )
        if not filtered_versions:
            if constraints != "any":
                try:
                    constraints = constraints.replace(" ", "")
                    versions_range = self.range_type.from_native(constraints)
                except Exception as _:
                    return filtered_versions
                for version in self.source_data["have"][dependency]:
                    check = True
                    try:
                        univers_version = self.version_type(version["release"])
                        check = check and univers_version in versions_range
                    except Exception as _:
                        continue
                    if check:
                        filtered_versions[version["count"]] = version[self.agregator]
            else:
                for version in self.source_data["have"][dependency]:
                    filtered_versions[version["count"]] = version[self.agregator]
            self.filtered_versions[f"{dependency}{constraints}"] = filtered_versions
        return filtered_versions

    def append_indirect_constraint(
        self, child: str, versions: list[int], parent: str, version: int
    ) -> None:
        if versions:
            self.childs.setdefault(
                self.group_versions_descendent(child, versions), {}
            ).setdefault(parent, set()).add(version)
            if child not in self.directs:
                self.parents.setdefault(child, {}).setdefault(parent, set()).add(
                    version
                )

    def build_direct_contraint(self, var: str, versions: list[int]) -> None:
        if versions:
            self.ctc_domain += f"{self.group_versions_descendent(var, versions)} "
        else:
            self.ctc_domain += "false "

    def build_indirect_constraints(self) -> None:
        for versions, _ in self.childs.items():
            for parent, parent_versions in _.items():
                self.ctc_domain += f"(=> {self.group_versions_ascendent(parent, list(parent_versions))} {versions}) "
        for child, _ in self.parents.items():
            for parent, parent_versions in _.items():
                self.ctc_domain += f"(=> (not {self.group_versions_ascendent(parent, list(parent_versions))}) (= {child} -1)) "

    def build_impact_constraints(self) -> None:
        for var, _ in self.ctcs.items():
            for impact, versions in _.items():
                self.ctc_domain += f"(=> {self.group_versions_ascendent(var, list(versions))} (= impact_{var} {impact})) "

    # TODO: Possibility to add new metrics
    def agregate(self, str_sum: str) -> str:
        match self.agregator:
            case "mean":
                return self.mean(str_sum)
            case "weighted_mean":
                return self.weighted_mean()
            case _:
                return ""

    def group_versions_descendent(self, var: str, versions: list[int]) -> str:
        constraints: list[str] = []
        current_group = [versions[0]]
        for i in range(1, len(versions)):
            if versions[i] == versions[i - 1] - 1:
                current_group.append(versions[i])
            else:
                constraints.append(
                    self.create_constraint_for_group_descendent(var, current_group)
                )
                current_group = [versions[i]]
        constraints.append(
            self.create_constraint_for_group_descendent(var, current_group)
        )
        return (
            constraints[0] if len(constraints) == 1 else f"(or {" ".join(constraints)})"
        )

    def group_versions_ascendent(self, var: str, versions: list[int]) -> str:
        constraints: list[str] = []
        current_group = [versions[0]]
        for i in range(1, len(versions)):
            if versions[i] == versions[i - 1] + 1:
                current_group.append(versions[i])
            else:
                constraints.append(
                    self.create_constraint_for_group_ascendent(var, current_group)
                )
                current_group = [versions[i]]
        constraints.append(
            self.create_constraint_for_group_ascendent(var, current_group)
        )
        return (
            constraints[0] if len(constraints) == 1 else f"(or {" ".join(constraints)})"
        )

    @staticmethod
    def create_constraint_for_group_descendent(var: str, group: list[int]) -> str:
        return (
            f"(= {var} {group[0]})"
            if len(group) == 1
            else f"(and (>= {var} {group[-1]}) (<= {var} {group[0]}))"
        )

    @staticmethod
    def create_constraint_for_group_ascendent(var: str, group: list[int]) -> str:
        return (
            f"(= {var} {group[0]})"
            if len(group) == 1
            else f"(and (>= {var} {group[0]}) (<= {var} {group[-1]}))"
        )

    @staticmethod
    def get_version_range_type(node_type: str) -> tuple[Version, VersionRange]:
        match node_type:
            case "PyPIPackage":
                return PypiVersion, PypiVersionRange
            case "NPMPackage":
                return SemverVersion, NpmVersionRange
            case "CargoPackage":
                return SemverVersion, CargoVersionRange
            case "MavenPackage":
                return MavenVersion, MavenVersionRange
            case "RubyGemsPackage":
                return RubygemsVersion, GemVersionRange
            case "NuGetPackage":
                return NugetVersion, NugetVersionRange
        return Version, VersionRange

    def mean(self, str_sum: str) -> str:
        if self.impacts:
            num_non_zero = self.sum_if()
            return f"(ite (= {num_non_zero} 0.0) 0.0 (/ {str_sum} {num_non_zero}))"
        return "0.0"

    def sum_if(self) -> str:
        sum_if = "(to_real (+ 0"
        for impact in self.impacts:
            sum_if += f" (ite (= {impact} 0.0) 0 1)"
        return sum_if + "))"

    def sum(self) -> str:
        return f"(+ 0 {" ".join(self.impacts)})"

    def weighted_mean(self) -> str:
        if self.impacts:
            divisors = (
                f"(+ 0 {" ".join([f"(* {x} (/ 1.0 10.0))" for x in self.impacts])})"
            )
            return f"(ite (= {divisors} 0.0) 0.0 (/ (+ 0 {" ".join([f"(* (^ {x} 2.0) (/ 1.0 10.0))" for x in self.impacts])}) {divisors}))"
        return "0.0"
