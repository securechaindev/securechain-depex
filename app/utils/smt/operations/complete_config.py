from z3 import Int, Optimize, sat, unknown

from app.utils.smt.config_sanitizer import config_sanitizer
from app.utils.smt.model import SMTModel


class CompleteConfig:
    def __init__(self, config: dict[str, int]) -> None:
        self.config: dict[str, int] = config
        self.result: list[dict[str, float | int]] | str = []

    def get_result(self) -> list[dict[str, float | int]] | str:
        return self.result

    def execute(self, model: SMTModel) -> None:
        solver = Optimize()
        solver.set("timeout", 3000)
        if model.func_obj_var is not None:
            cvss_f = model.func_obj_var
            solver.minimize(cvss_f)
        solver.add(model.domain)
        for package, count in self.config.items():
            solver.add(Int(package) == count)
        while solver.check() == sat:
            config = solver.model()
            sanitized_config = config_sanitizer(config)
            if isinstance(self.result, list):
                self.result.append(sanitized_config)
            break
        if solver.check() == unknown:
            self.result = (
                "Execution timed out after 3 seconds. The complexity of the model is too high, try lowering the maximum level of the graph."
            )
