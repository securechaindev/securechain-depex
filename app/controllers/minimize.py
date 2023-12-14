from z3 import Or, Optimize, sat

from flamapy.core.operations import Operation
from flamapy.metamodels.smt_metamodel.models import PySMTModel
from app.controllers.sanitizer import config_sanitizer


class MinimizeImpact(Operation):
    def __init__(self, limit: int) -> None:
        self.limit: int = limit
        self.result: list[dict[str, float | int]] = []

    def get_result(self) -> list[dict[str, float | int]]:
        return self.result

    def execute(self, model: PySMTModel) -> None:
        solver = Optimize()
        if model.func_obj_var is not None:
            cvss_f = model.func_obj_var
            solver.minimize(cvss_f)
        solver.add(model.domain)
        while len(self.result) < self.limit and solver.check() == sat:
            config = solver.model()
            sanitized_config = config_sanitizer(config)
            self.result.append(sanitized_config)

            block = []
            for var in config:
                if str(var) != "/0":
                    variable = var()
                    if "CVSS" not in str(variable):
                        block.append(config[var] != variable)

            solver.add(Or(block))
