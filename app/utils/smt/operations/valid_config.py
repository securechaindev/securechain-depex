from z3 import Int, Solver, sat, unknown

from app.utils.smt.model import SMTModel


async def execute_valid_config(model: SMTModel, config: dict[str, int]) -> bool | str:
    solver = Solver()
    solver.set("timeout", 3000)
    result = []
    solver.add(model.domain)
    for package, serial_number in config.items():
        solver.add(Int(package) == serial_number)
    result = solver.check() == sat
    if solver.check() == unknown:
        result = (
            "Execution timed out after 3 seconds. The complexity of the model is too high, try lowering the maximum level of the graph."
        )
    return result
