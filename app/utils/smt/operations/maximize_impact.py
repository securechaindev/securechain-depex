from z3 import Optimize, Or, sat, unknown

from app.utils.smt.config_sanitizer import config_sanitizer
from app.utils.smt.model import SMTModel


class MaximizeImpact:
    def __init__(self, limit: int) -> None:
        self.limit: int = limit
        self.result: list[dict[str, float | int]] | str = []

    def get_result(self) -> list[dict[str, float | int]] | str:
        return self.result

    def execute(self, model: SMTModel) -> None:
        solver = Optimize()
        solver.set("timeout", 3000)
        if model.func_obj is not None:
            impact = model.func_obj
            solver.maximize(impact)
        solver.add(model.domain)
        while len(self.result) < self.limit and solver.check() == sat:
            config = solver.model()
            sanitized_config = config_sanitizer(config)
            if isinstance(self.result, list):
                self.result.append(sanitized_config)
            block = []
            for var in config:
                if str(var) != "/0":
                    variable = var()
                    if "CVSS" not in str(variable):
                        block.append(config[var] != variable)
            solver.add(Or(block))
        if solver.check() == unknown:
            self.result = (
                "Execution timed out after 3 seconds. The complexity of the model is too high, try lowering the maximum level of the graph."
            )
