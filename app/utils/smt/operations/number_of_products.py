from z3 import Or, Solver, sat, unknown
from app.utils.smt.model import SMTModel


class NumberOfProducts():
    def __init__(self) -> None:
        self.result: int | str = 0

    def get_result(self) -> int | str:
        return self.result

    def execute(self, model: SMTModel) -> None:
        solver = Solver()
        solver.set("timeout", 3000)
        solver.add(model.domain)
        while solver.check() == sat:
            config = solver.model()
            block = []
            for var in config:
                if str(var) != "/0":
                    variable = var()
                    if "CVSS" not in str(variable):
                        block.append(config[var] != variable)
            solver.add(Or(block))
            if isinstance(self.result, int):
                self.result += 1
        if solver.check() == unknown:
            self.result = (
                "Execution timed out after 3 seconds. "
                "The complexity of the model is too high, "
                "try lowering the maximum level of the graph."
            )