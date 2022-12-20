from z3 import Int, Solver, sat, ModelRef, Optimize, Abs

from flamapy.core.operations import Operation
from flamapy.metamodels.smt_metamodel.models import PySMTModel
from flamapy.metamodels.smt_metamodel.utils import config_sanitizer


class ValidConfig(Operation):

    def __init__(
        self,
        file_name: str,
        config: dict[str, int]
    ) -> None:
        self.file_name: str = file_name
        self.config: dict[str, int] = config
        self.result: bool = True

    def get_result(self) -> bool:
        return self.result

    def execute(self, model: PySMTModel) -> None:
        formula = model.domains[self.file_name]
        solver = Solver()
        solver.add(formula)
        for package, count in self.config.items():
            solver.add(Int(package) == count)
        self.result = solver.check() == sat


class CompleteConfig(Operation):

    def __init__(
        self,
        file_name: str,
        config: dict[str, int]
    ) -> None:
        self.file_name: str = file_name
        self.config: dict[str, int] = config
        self.result: list[ModelRef] = []

    def get_result(self) -> list[ModelRef]:
        return self.result

    def execute(self, model: PySMTModel) -> None:
        solver = Optimize()
        if model.cvvs:
            cvss_f = model.cvvs[self.file_name]
            solver.minimize(cvss_f)

        formula = model.domains[self.file_name]
        solver.add(formula)
        for package, count in self.config.items():
            solver.add(Int(package) == count)

        while solver.check() == sat:
            config = solver.model()
            sanitized_config = config_sanitizer(config)
            self.result.append(sanitized_config)
            break


class ConfigByImpact(Operation):

    def __init__(
        self,
        file_name: str,
        impact: int
    ) -> None:
        self.file_name: str = file_name
        self.impact: int = impact
        self.result: list[ModelRef] = []

    def get_result(self) -> list[ModelRef]:
        return self.result

    def execute(self, model: PySMTModel) -> None:
        solver = Optimize()
        if model.cvvs:
            cvss_f = model.cvvs[self.file_name]
            obj = Abs(cvss_f - self.impact)
            solver.minimize(obj)

        formula = model.domains[self.file_name]
        solver.add(formula)
        while solver.check() == sat:
            config = solver.model()
            sanitized_config = config_sanitizer(config)
            self.result.append(sanitized_config)
            break