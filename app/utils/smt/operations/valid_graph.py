from z3 import Solver, sat, unknown

from app.utils.smt.model import SMTModel


async def execute_valid_graph(model: SMTModel) -> bool | str:
    solver = Solver()
    solver.set("timeout", 3000)
    solver.add(model.domain)
    result = solver.check() == sat
    if solver.check() == unknown:
        result = (
            "Execution timed out after 3 seconds. The complexity of the model is too high, try lowering the maximum level of the graph."
        )
    return result
