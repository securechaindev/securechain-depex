from typing import Any

from z3 import And, ArithRef, BoolRef, Implies, Int, Or, Real, Not, If

from univers.versions import Version, PypiVersion, SemverVersion, MavenVersion, InvalidVersion
from univers.version_range import (
    VersionRange,
    PypiVersionRange,
    NpmVersionRange,
    MavenVersionRange
)

from flamapy.core.transformations import Transformation
from flamapy.metamodels.smt_metamodel.models.pysmt_model import PySMTModel


class GraphToSMT(Transformation):

    @staticmethod
    def get_source_extension() -> str:
        return 'neo4j'

    @staticmethod
    def get_destination_extension() -> str:
        return 'smt'

    def __init__(
        self,
        source_data: dict[str, Any],
        file_name: str,
        package_manager: str,
        agregator: str
    ) -> None:
        self.source_data: dict[str, list[dict[str, Any]]] = source_data
        self.file_name: str = file_name
        self.agregator: str = agregator
        self.destination_model: PySMTModel = PySMTModel()
        self.version_type, self.range_type = self.get_version_range_type(package_manager)
        self.vars: dict[str, ArithRef] = {}
        self.childs: dict[ArithRef, dict[ArithRef, set[int]]] = {}
        self.parents: dict[ArithRef, dict[ArithRef, set[int]]] = {}
        self.directs: list[str] = []
        self.domain: list[BoolRef] = []
        self.ctcs: dict[ArithRef, dict[float, set[int]]] = {}
        self.filtered_versions: dict[tuple(str, str), dict[int, int]] = {}

    def transform(self) -> None:
        impacts: list[ArithRef] = []
        for rel_requires in self.source_data['requires']:
            if rel_requires['parent_version_name'] == None:
                impacts.extend(self.transform_direct_package(rel_requires))
            else:
                impacts.extend(self.transform_indirect_package(rel_requires))
        self.build_indirect_constraints()
        self.build_impact_constraints()
        self.domain.append(Real('file_risk_' + self.file_name) == self.agregate(impacts))
        func_obj_var = Real('func_obj_' + self.file_name)
        self.domain.append(func_obj_var == sum(impacts))
        self.destination_model.domain = And(self.domain)
        self.destination_model.func_obj_var = func_obj_var
        file = open('model.txt', 'w')
        file.write(str(self.domain))
        file.close()

    def transform_direct_package(self, rel_requires: dict[str, Any]) -> list[ArithRef]:
        impacts: list[ArithRef] = []
        filtered_versions = self.filter_versions(
            rel_requires['dependency'],
            rel_requires['constraints']
        )
        if filtered_versions:
            self.directs.append(rel_requires['dependency'])
            if rel_requires['dependency'] not in self.vars:
                var = Int(rel_requires['dependency'])
                self.vars[rel_requires['dependency']] = var
                cvss_p_name = 'impact_' + rel_requires['dependency']
                cvss_p_var = Real(cvss_p_name)
                self.vars[cvss_p_name] = cvss_p_var
                impacts.append(cvss_p_var)
            else:
                var = self.vars[rel_requires['dependency']]
                cvss_p_var = self.vars['impact_' + rel_requires['dependency']]
            self.build_direct_contraint(var, filtered_versions.keys())
            self.transform_versions(filtered_versions, var, cvss_p_var)
        return impacts

    def transform_indirect_package(
        self,
        rel_requires: dict[str, Any]
    ) -> list[ArithRef]:
        impacts: list[ArithRef] = []
        filtered_versions = self.filter_versions(
            rel_requires['dependency'],
            rel_requires['constraints']
        )
        parent = rel_requires['parent_version_name']
        if filtered_versions and parent in self.vars:
            if rel_requires['dependency'] not in self.vars:
                var = Int(rel_requires['dependency'])
                self.vars[rel_requires['dependency']] = var
                cvss_p_name = 'impact_' + rel_requires['dependency']
                cvss_p_var = Real(cvss_p_name)
                self.vars[cvss_p_name] = cvss_p_var
                impacts.append(cvss_p_var)
                self.ctcs.setdefault((var, cvss_p_var), {}).setdefault(0., set()).add(-1)
            else:
                var = self.vars[rel_requires['dependency']]
                cvss_p_var = self.vars['impact_' + rel_requires['dependency']]
            self.append_indirect_constraint(
                var,
                filtered_versions.keys(),
                self.vars[parent],
                rel_requires['parent_count']
            )
            self.transform_versions(filtered_versions, var, cvss_p_var)
        return impacts

    def transform_versions(
        self,
        versions: dict[int, int],
        var: ArithRef,
        cvss_p_var: ArithRef
    ) -> None:
        for version, impact in versions.items():
            self.ctcs.setdefault((var, cvss_p_var), {}).setdefault(
                impact,
                set()
            ).add(version)

    def filter_versions(self, dependency: str, constraints: str) -> list[dict[int, int]]:
        filtered_versions = self.filtered_versions.setdefault((dependency, constraints), {})
        if not filtered_versions:
            if constraints != "any":
                try:
                    constraints = constraints.replace(" ", "")
                    versions_range = self.range_type.from_native(constraints)
                except Exception as _:
                    return filtered_versions
            for version in self.source_data["have"][dependency]:
                check = True
                if constraints != "any":
                    try:
                        univers_version = self.version_type(version['release'])
                        check = check and univers_version in versions_range
                    except Exception as _:
                        continue
                if check:
                    filtered_versions[version['count']] = version[self.agregator]
            self.filtered_versions[(dependency, constraints)] = filtered_versions
        return filtered_versions

    def append_indirect_constraint(
        self,
        child: ArithRef,
        versions: list[int],
        parent: ArithRef,
        version: int
    ) -> None:
        if versions:
            self.childs.setdefault(self.group_versions_descendent(child, list(versions)), {}).setdefault(parent, set()).add(version)
            if str(child) not in self.directs:
                self.parents.setdefault(child, {}).setdefault(parent, set()).add(version)

    def build_direct_contraint(self, var: ArithRef, versions: list[int]) -> None:
        if versions:
            self.domain.append(self.group_versions_descendent(var, list(versions)))
        else:
            self.domain.append(False)

    def build_indirect_constraints(self) -> None:
        for versions, _ in self.childs.items():
            for parent, parent_versions in _.items():
                self.domain.append(Implies(self.group_versions_ascendent(parent, list(parent_versions)), versions))
        for child, _ in self.parents.items():
            for parent, parent_versions in _.items():
                self.domain.append(Implies(Not(self.group_versions_ascendent(parent, list(parent_versions))), child == -1))

    def build_impact_constraints(self) -> None:
        for vars_, _ in self.ctcs.items():
            for impact, versions in _.items():
                self.domain.append(
                    Implies(self.group_versions_ascendent(vars_[0], list(versions)), vars_[1] == impact)
                )

    # TODO: Possibility to add new metrics
    def agregate(
        self,
        impacts: list[ArithRef],
    ) -> ArithRef:
        match self.agregator:
            case 'mean':
                return self.mean(impacts)
            case 'weighted_mean':
                return self.weighted_mean(impacts)

    def group_versions_descendent(self, var: ArithRef, versions: list[int]) -> BoolRef:
        constraints: list[BoolRef] = []
        current_group = [versions[0]]
        for i in range(1, len(versions)):
            if versions[i] == versions[i-1] - 1:
                current_group.append(versions[i])
            else:
                constraints.append(self.create_constraint_for_group_descendent(var, current_group))
                current_group = [versions[i]]
        constraints.append(self.create_constraint_for_group_descendent(var, current_group))
        return constraints[0] if len(constraints) == 1 else Or(constraints)

    def group_versions_ascendent(self, var: ArithRef, versions: list[int]) -> BoolRef:
        constraints: list[BoolRef] = []
        current_group = [versions[0]]
        for i in range(1, len(versions)):
            if versions[i] == versions[i-1] + 1:
                current_group.append(versions[i])
            else:
                constraints.append(self.create_constraint_for_group_ascendent(var, current_group))
                current_group = [versions[i]]
        constraints.append(self.create_constraint_for_group_ascendent(var, current_group))
        return constraints[0] if len(constraints) == 1 else Or(constraints)

    @staticmethod
    def create_constraint_for_group_descendent(var: ArithRef, group: list[int]) -> BoolRef:
        return var == group[0] if len(group) == 1 else And(var >= group[-1], var <= group[0])

    @staticmethod
    def create_constraint_for_group_ascendent(var: ArithRef, group: list[int]) -> BoolRef:
        return var == group[0] if len(group) == 1 else And(var >= group[0], var <= group[-1])

    @staticmethod
    def get_version_range_type(package_manager: str) -> tuple[Version, VersionRange]:
        match package_manager:
            case 'PIP':
                return PypiVersion, PypiVersionRange
            case 'NPM':
                return SemverVersion, NpmVersionRange
            case 'MVN':
                return MavenVersion, MavenVersionRange
        return PypiVersion, PypiVersionRange

    @staticmethod
    def mean(impacts: list[ArithRef]) -> ArithRef:
        if impacts:
            num_non_zero = sum([If(val == 0, 0, 1) for val in impacts])
            return If(num_non_zero == 0., 0., sum(impacts) / num_non_zero)
        return 0.

    @staticmethod
    def weighted_mean(impacts: list[ArithRef]) -> ArithRef:
        if impacts:
            divisors = sum([val * 0.1 for val in impacts])
            return If(divisors == 0., 0, sum([val**2 * 0.1 for val in impacts]) / divisors)
        return 0.