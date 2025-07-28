from typing import Any

from z3 import ArithRef, BoolRef, Real, parse_smt2_string

from app.utils.others import filter_versions


class SMTModel:
    def __init__(self, source_data: dict[str, Any], node_type: str, agregator: str) -> None:
        self.source_data = source_data
        self.agregator = agregator
        self.node_type = node_type
        self.domain: BoolRef = None
        self.func_obj: ArithRef = None
        self.impacts: set[str] = set()
        self.childs: dict[str, dict[str, set[int]]] = {}
        self.parents: dict[str, dict[str, set[int]]] = {}
        self.directs: list[str] = []
        self.var_domain: set[str] = set()
        self.indirect_vars: set[str] = set()
        self.ctc_domain: str = ""
        self.ctcs: dict[str, dict[float, set[int]]] = {}
        self.constraint_cache: dict[tuple[str, frozenset[int]], str] = {}
        self.filtered_versions: dict[str, list[int]] = {}


    async def convert(self, model_text: str) -> None:
            self.domain = parse_smt2_string(model_text)
            self.func_obj = Real(f"file_risk_{self.source_data['name']}")


    async def transform(self) -> str:
        for key in ["direct", "indirect"]:
            for require in self.source_data["require"].get(key, []):
                await getattr(self, f"transform_{key}_package")(require)
        file_risk_name = f"file_risk_{self.source_data['name']}"
        self.var_domain.add(f"(declare-const {file_risk_name} Real)")
        await self.build_indirect_constraints()
        await self.build_impact_constraints()
        str_sum = await self.sum()
        self.ctc_domain += f"(= {file_risk_name} {str_sum})"
        for indirect_var in self.indirect_vars:
            self.var_domain.add(f"(declare-const {indirect_var} Int)")
            self.var_domain.add(f"(declare-const impact_{indirect_var} Real)")
        model_text = f"{' '.join(self.var_domain)} (assert (and {self.ctc_domain}))"
        self.domain = parse_smt2_string(model_text)
        self.func_obj = Real(file_risk_name)
        return model_text


    async def transform_direct_package(self, require: dict[str, Any]) -> None:
        filtered_versions = await filter_versions(self.node_type, self.source_data["have"][require["package"]], require["constraints"])
        versions_impacts: dict[int, int] = {version.get("serial_number"): version[self.agregator] for version in filtered_versions}
        versions_names = list(versions_impacts.keys())
        self.directs.append(require["package"])
        var_impact = f"impact_{require['package']}"
        self.impacts.add(var_impact)
        self.var_domain.add(f"(declare-const {require['package']} Int)")
        self.var_domain.add(f"(declare-const {var_impact} Real)")
        await self.build_direct_contraint(
            require["package"], versions_names
        )
        self.filtered_versions[require["package"]] = versions_names
        await self.transform_versions(versions_impacts, require["package"])


    async def transform_indirect_package(self, require: dict[str, Any]) -> None:
        filtered_versions = await filter_versions(self.node_type, self.source_data["have"][require["package"]], require["constraints"])
        versions_impacts: dict[int, int] = {version.get("serial_number"): version[self.agregator] for version in filtered_versions}
        versions_names = list(versions_impacts.keys())
        await self.append_indirect_constraint(
            require["package"],
            versions_names,
            require["parent_version_name"],
            require["parent_serial_number"],
        )
        self.filtered_versions[require["package"]] = versions_names
        await self.transform_versions(versions_impacts, require["package"], require)


    async def transform_versions(self, versions: dict[int, int], var: str, require: dict[str, Any] | None = None) -> None:
        if not require or require["parent_serial_number"] in self.filtered_versions[require["parent_version_name"]]:
            _default = {}
            if require:
                self.impacts.add(f"impact_{require['package']}")
                self.indirect_vars.add(var)
                self.indirect_vars.add(require["parent_version_name"])
                _default = {.0: {-1}}
            for version, impact in versions.items():
                self.ctcs.setdefault(var, _default).setdefault(impact, set()).add(version)


    async def append_indirect_constraint(
        self, child: str, versions: list[int], parent: str, version: int
    ) -> None:
        if versions:
            if version in self.filtered_versions[parent]:
                self.childs.setdefault(
                    await self.group_versions(child, versions, False), {}
                ).setdefault(parent, set()).add(version)
                if child not in self.directs:
                    self.parents.setdefault(child, {}).setdefault(parent, set()).add(
                        version
                    )


    async def build_direct_contraint(self, var: str, versions: list[int]) -> None:
        if versions:
            self.ctc_domain += f"{await self.group_versions(var, versions, False)} "
        else:
            self.ctc_domain += "false "


    async def build_indirect_constraints(self) -> None:
        for versions, _ in self.childs.items():
            for parent, parent_versions in _.items():
                self.ctc_domain += f"(=> {await self.group_versions(parent, list(parent_versions), True)} {versions}) "
        for child, _ in self.parents.items():
            for parent, parent_versions in _.items():
                self.ctc_domain += f"(=> (not {await self.group_versions(parent, list(parent_versions), True)}) (= {child} -1)) "


    async def build_impact_constraints(self) -> None:
        for var, _ in self.ctcs.items():
            for impact, versions in _.items():
                self.ctc_domain += f"(=> {await self.group_versions(var, list(versions), True)} (= impact_{var} {impact})) "


    async def group_versions(
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
                constraints.append(await self.create_constraint_for_group(var, current_group, ascending))
                current_group = [versions[i]]
        constraints.append(await self.create_constraint_for_group(var, current_group, ascending))
        return constraints[0] if len(constraints) == 1 else f"(or {' '.join(constraints)})"


    @staticmethod
    async def create_constraint_for_group(var: str, group: list[int], ascending: bool) -> str:
        if len(group) == 1:
            return f"(= {var} {group[0]})"
        min_val, max_val = (group[0], group[-1]) if ascending else (group[-1], group[0])
        return f"(and (>= {var} {min_val}) (<= {var} {max_val}))"


    async def sum(self) -> str:
        return f"(+ {' '.join(self.impacts)})" if self.impacts else "0.0"
