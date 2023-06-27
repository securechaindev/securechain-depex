from typing import Any

from operator import eq, lt, gt, le, ge

from z3 import And, ArithRef, BoolRef, Implies, Int, Or, Real, Not

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
        agregator: str | None = None
    ) -> None:
        self.source_data: dict[str, Any] = source_data
        self.file_name: str = file_name
        self.package_manager: str = package_manager
        self.agregator: str | None = agregator
        self.destination_model: PySMTModel = PySMTModel()
        self.dependency_versions: dict[str, Any] = self.match_dependency_versions()
        self.version_type, self.range_type = self.get_version_range_type()
        self.vars: dict[str, ArithRef] = {}
        self.childs: dict[BoolRef, list[BoolRef]] = {}
        self.parents: dict[ArithRef, list[BoolRef]] = {}
        self.directs: list[str] = []
        self.cvss_p: list[ArithRef] = []
        self.domain: list[BoolRef] = []
        self.distributions: list[str] = []
        self.ctcs: list[BoolRef] = []
        self.operations = {
            '==': eq,
            '<': lt,
            '>': gt,
            '<=': le,
            '>=': ge
        }

    def match_dependency_versions(self) -> dict[str, Any]:
        dependency_versions: dict[str, Any] = {}
        for rel_have in self.source_data['have']:
            if rel_have['dependency'] in dependency_versions:
                dependency = rel_have.pop('dependency')
                dependency_versions[dependency].append(rel_have)
            else:
                dependency = rel_have.pop('dependency')
                dependency_versions[dependency] = [rel_have]
        return dependency_versions

    def transform(self) -> None:
        for rel_requires in self.source_data['requires']:
            if rel_requires['parent_type'] == 'RequirementFile':
                self.transform_direct_package(rel_requires)
            else:
                self.transform_indirect_package(rel_requires)
        self.build_indirect_constraints()
        self.domain.extend(self.ctcs)

        cvss_f_var = Real('CVSS' + self.file_name)
        agregator_impact = self.agregate(self.cvss_p) if self.cvss_p else 0.
        self.domain.append(cvss_f_var == agregator_impact)

        func_obj_var = Real('func_obj_' + self.file_name)
        func_obj_impact = self.obj_func(self.cvss_p) if self.cvss_p else 0.
        self.domain.append(func_obj_var == func_obj_impact)

        self.destination_model.domain = And(self.domain)
        self.destination_model.func_obj_var = func_obj_var

    def transform_direct_package(self, rel_requires: dict[str, Any]) -> None:
        self.directs.append(rel_requires['dependency'])
        if rel_requires['dependency'] not in self.vars:
            var = Int(rel_requires['dependency'])
            self.vars[rel_requires['dependency']] = var

            cvss_p_name = 'CVSS' + rel_requires['dependency']
            cvss_p_var = Real(cvss_p_name)
            self.vars[cvss_p_name] = cvss_p_var
            self.cvss_p.append(cvss_p_var)
        else:
            var = self.vars[rel_requires['dependency']]
            cvss_p_var = self.vars['CVSS' + rel_requires['dependency']]

        filtered_versions = self.filter_versions(
            rel_requires['dependency'],
            rel_requires['constraints']
        )

        self.build_direct_contraint(var, filtered_versions)

        self.transform_versions(filtered_versions, var, cvss_p_var)

    def transform_indirect_package(
        self,
        rel_requires: dict[str, Any]
    ) -> None:
        if rel_requires['dependency'] not in self.vars:
            var = Int(rel_requires['dependency'])
            self.vars[rel_requires['dependency']] = var

            cvss_p_name = 'CVSS' + rel_requires['dependency']
            cvss_p_var = Real(cvss_p_name)
            self.vars[cvss_p_name] = cvss_p_var
            self.cvss_p.append(cvss_p_var)

            ctc = Implies(var == -1, cvss_p_var == 0.)
            self.ctcs.append(ctc)
        else:
            var = self.vars[rel_requires['dependency']]
            cvss_p_var = self.vars['CVSS' + rel_requires['dependency']]

        parent_name = self.get_parent_name(rel_requires['parent_id'])
        parent = self.vars[parent_name]

        filtered_versions = self.filter_versions(
            rel_requires['dependency'],
            rel_requires['constraints']
        )

        self.append_indirect_constraint(
            var,
            filtered_versions,
            parent,
            rel_requires['parent_count']
        )

        self.transform_versions(filtered_versions, var, cvss_p_var)

    def transform_versions(
        self,
        versions: list[dict[str, Any]],
        var: ArithRef,
        cvss_p_var: ArithRef
    ) -> None:
        for version in versions:
            key = str(var) + '-' + str(version['count'])
            if key not in self.distributions:
                match self.agregator:
                    case 'mean':
                        v_impact = version['mean']
                    case 'weighted_mean':
                        v_impact = version['weighted_mean']
                    case _:
                        v_impact = version['mean']
                ctc = Implies(var == version['count'], cvss_p_var == v_impact)
                self.ctcs.append(ctc)
                self.distributions.append(key)

    def get_parent_name(self, version_id: str) -> str:
        for dependency, versions in self.dependency_versions.items():
            for version in versions:
                if version['id'] == version_id:
                    return dependency
        return ''

    def filter_versions(self, dependency: str, constraints: str) -> list[dict[str, Any]]:
        filtered_versions = []
        if constraints != 'any':
            for version in self.dependency_versions[dependency]:
                check = True
                if self.package_manager == 'PIP':
                    for constraint in constraints.split(','):
                        versions_range = self.range_type.from_native(constraint)
                        check = check and self.version_type(version['release']) in versions_range
                else:
                    versions_range = self.range_type.from_native(constraints)
                    check = check and self.version_type(version['release']) in versions_range
                if check:
                    filtered_versions.append(version)
            return filtered_versions
        return self.dependency_versions[dependency]

    def build_direct_contraint(self, var: ArithRef, versions: list[dict[str, Any]]) -> None:
        constraint = [var == version['count'] for version in versions]
        if constraint:
            self.domain.append(Or(constraint))

    def append_indirect_constraint(
        self,
        var: ArithRef,
        versions: list[dict[str, Any]],
        parent: ArithRef,
        version: int
    ) -> None:
        parts = [var == version['count'] for version in versions]
        if parts:
            versions = Or(parts)
            if versions in self.childs:
                self.childs[versions].append(parent == version)
            else:
                self.childs[versions] = [parent == version]

        if str(var) not in self.directs:
            if var in self.parents:
                self.parents[var].append(parent == version)
            else:
                self.parents[var] = [parent == version]

    def build_indirect_constraints(self) -> None:
        for versions, parents in self.childs.items():
            self.domain.append(Implies(Or(parents), versions))
        for var, parents in self.parents.items():
            self.domain.append(Implies(Not(Or(parents)), var == -1))

    def get_version_range_type(self):
        match self.package_manager:
            case 'PIP':
                from univers.versions import PypiVersion
                from univers.version_range import PypiVersionRange
                return (PypiVersion, PypiVersionRange)
            case 'NPM':
                from univers.versions import SemverVersion
                from univers.version_range import NpmVersionRange
                return (SemverVersion, NpmVersionRange)
            case 'MVN':
                from univers.versions import MavenVersion
                from univers.version_range import MavenVersionRange
                return (MavenVersion, MavenVersionRange)
            case _:
                from univers.versions import PypiVersion
                from univers.version_range import PypiVersionRange
                return (PypiVersion, PypiVersionRange)

    # TODO: Posibilidad de añadir nuevas métricas
    def agregate(
        self,
        impacts: list[ArithRef],
    ) -> ArithRef:
        match self.agregator:
            case 'mean':
                return self.mean(impacts)
            case 'weighted_mean':
                return self.weighted_mean(impacts)
            case _:
                return self.mean(impacts)

    @staticmethod
    def obj_func(problems: list[ArithRef]) -> ArithRef:
        return sum(problems)

    @staticmethod
    def mean(impacts: list[ArithRef]) -> ArithRef:
        if impacts:
            return sum(impacts) / len(impacts)
        return 0.

    @staticmethod
    def weighted_mean(impacts: list[ArithRef]) -> ArithRef:
        if impacts:
            dividends = []
            divisors = []

            for var in impacts:
                dividends.append(var**2 * 0.1)
                divisors.append(var * 0.1)

            return sum(dividends) / sum(divisors)
        return 0.