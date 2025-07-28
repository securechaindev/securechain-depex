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
    def __init__(self, source_data: dict[str, Any], node_type: str, agregator: str) -> None:
        self.source_data = source_data
        self.agregator = agregator
        self.version_type, self.range_type = self.get_version_range_type(node_type)
        self.domain: BoolRef = None
        self.func_obj: ArithRef = None
        self.impacts: set[str] = set()
        self.childs: dict[str, dict[str, set[int]]] = {}
        self.parents: dict[str, dict[str, set[int]]] = {}
        self.directs: list[str] = []
        self.var_domain: set[str] = set()
        self.ctc_domain: str = ""
        self.ctcs: dict[str, dict[float, set[int]]] = {}
        self.filtered_versions: dict[str, dict[int, int]] = {}
        self.constraint_cache: dict[tuple[str, frozenset[int]], str] = {}


    def convert(self, model_text: str) -> None:
        self.domain = parse_smt2_string(model_text)
        self.func_obj = Real(f"file_risk_{self.source_data['name']}")


    def transform(self) -> str:
        for key in ["direct", "indirect"]:
            for require in self.source_data["require"].get(key, []):
                getattr(self, f"transform_{key}_package")(require)

        file_risk_name = f"file_risk_{self.source_data['name']}"
        self.var_domain.add(f"(declare-const {file_risk_name} Real)")

        self.build_indirect_constraints()
        self.build_impact_constraints()

        str_sum = self.sum()
        self.ctc_domain += f"(= {file_risk_name} {str_sum})"

        model_text = f"{' '.join(self.var_domain)} (assert (and {self.ctc_domain}))"
        self.domain = parse_smt2_string(model_text)
        self.func_obj = Real(file_risk_name)

        return model_text


    def transform_direct_package(self, require: dict[str, Any]) -> None:
        filtered_versions = self.filter_versions(require["package"], require["constraints"])
        if filtered_versions:
            self.directs.append(require["package"])
            var_impact = f"impact_{require['package']}"
            self.impacts.add(var_impact)
            self.var_domain.add(f"(declare-const {require["package"]} Int)")
            self.var_domain.add(f"(declare-const {var_impact} Real)")
            self.build_direct_contraint(require["package"], list(filtered_versions.keys()))
            self.transform_versions(filtered_versions, require["package"], "direct")


    def transform_indirect_package(self, require: dict[str, Any]) -> None:
        filtered_versions = self.filter_versions(require["package"], require["constraints"])
        if filtered_versions:
            var_impact = f"impact_{require["package"]}"
            self.impacts.add(var_impact)
            self.var_domain.add(f"(declare-const {require["package"]} Int)")
            self.var_domain.add(f"(declare-const {var_impact} Real)")
            self.var_domain.add(f"(declare-const {require["parent_version_name"]} Int)")
            self.append_indirect_constraint(
                require["package"],
                list(filtered_versions.keys()),
                require["parent_version_name"],
                require["parent_serial_number"],
            )
            self.transform_versions(filtered_versions, require["package"], "indirect")


    def transform_versions(self, versions: dict[int, int], var: str, _type: str) -> None:
        for version, impact in versions.items():
            if _type == "direct":
                self.ctcs.setdefault(var, {}).setdefault(impact, set()).add(version)
            elif _type == "indirect":
                self.ctcs.setdefault(var, {.0: {-1}}).setdefault(impact, set()).add(version)


    def filter_versions(self, package: str, constraints: str) -> dict[int, int]:
        key = f"{package}{constraints}"
        filtered_versions = self.filtered_versions.setdefault(key, {})
        if not filtered_versions:
            try:
                constraints = constraints.replace(" ", "")
                versions_range = self.range_type.from_native(constraints) if constraints != "any" else None
                for version in self.source_data["have"][package]:
                    if constraints == "any" or self.version_type(version["name"]) in versions_range:
                        filtered_versions[version["serial_number"]] = version[self.agregator]
            except Exception:
                pass
        return filtered_versions


    def append_indirect_constraint(self, child: str, versions: list[int], parent: str, version: int) -> None:
        if versions:
            group = self.group_versions(child, versions)
            self.childs.setdefault(group, {}).setdefault(parent, set()).add(version)
            if child not in self.directs:
                self.parents.setdefault(child, {}).setdefault(parent, set()).add(version)


    def build_direct_contraint(self, var: str, versions: list[int]) -> None:
        self.ctc_domain += f"{self.group_versions(var, versions)} " if versions else "false "


    def build_indirect_constraints(self) -> None:
        for group_expr, parents in self.childs.items():
            for parent, parent_versions in parents.items():
                self.ctc_domain += f"(=> {self.group_versions(parent, list(parent_versions))} {group_expr}) "
        for child, parents in self.parents.items():
            for parent, parent_versions in parents.items():
                self.ctc_domain += f"(=> (not {self.group_versions(parent, list(parent_versions))}) (= {child} -1)) "


    def build_impact_constraints(self) -> None:
        for var, impacts in self.ctcs.items():
            for impact, versions in impacts.items():
                self.ctc_domain += f"(=> {self.group_versions(var,  list(versions))} (= impact_{var} {impact})) "

    
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


    def sum(self) -> str:
        return f"(+ {' '.join(self.impacts)})" if self.impacts else "0.0"


    @staticmethod
    def get_version_range_type(node_type: str) -> tuple[Version, VersionRange]:
        return {
            "PyPIPackage": (PypiVersion, PypiVersionRange),
            "NPMPackage": (SemverVersion, NpmVersionRange),
            "CargoPackage": (SemverVersion, CargoVersionRange),
            "MavenPackage": (MavenVersion, MavenVersionRange),
            "RubyGemsPackage": (RubygemsVersion, GemVersionRange),
            "NuGetPackage": (NugetVersion, NugetVersionRange),
        }.get(node_type, (Version, VersionRange))
