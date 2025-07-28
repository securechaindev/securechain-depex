from z3 import Int, Optimize, sat, unknown

from app.utils.smt.config_sanitizer import config_sanitizer
from app.utils.smt.model import SMTModel


async def execute_complete_config(model: SMTModel, config: dict[str, int]) -> list[dict[str, float | int]] | str:
    solver = Optimize()
    solver.set("timeout", 3000)
    result = []
    if model.func_obj is not None:
        impact = model.func_obj
        solver.minimize(impact)
    solver.add(model.domain)
    for package, serial_number in config.items():
        solver.add(Int(package) == serial_number)
    while solver.check() == sat:
        config = solver.model()
        sanitized_config = await config_sanitizer(model.node_type, config)
        result.append(sanitized_config)
        break
    if solver.check() == unknown:
        result = (
            "Execution timed out after 3 seconds. The complexity of the model is too high, try lowering the maximum level of the graph."
        )
    return result
