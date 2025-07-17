from z3 import And, Or, Solver, sat, unknown

from app.utils.smt.config_sanitizer import config_sanitizer
from app.utils.smt.model import SMTModel


class FilterConfigs:
    def __init__(self, max_threshold: float, min_threshold: float, limit: int) -> None:
        self.max_threshold: float = max_threshold
        self.min_threshold: float = min_threshold
        self.limit: int = limit
        self.result: list[dict[str, float | int]] | str = []

    def get_result(self) -> list[dict[str, float | int]] | str:
        return self.result

    def execute(self, model: SMTModel) -> None:
        if model.func_obj_var is not None:
            cvss_f = model.func_obj_var
            max_ctc = cvss_f <= self.max_threshold
            min_ctc = cvss_f >= self.min_threshold
        solver = Solver()
        solver.set("timeout", 3000)
        solver.add(And([model.domain, max_ctc, min_ctc]))
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
