from z3 import Abs, Optimize, sat, unknown

from app.utils.smt.config_sanitizer import config_sanitizer
from app.utils.smt.model import SMTModel


async def execute_config_by_impact(model: SMTModel, impact: int) -> list[dict[str, float | int]] | str:
    solver = Optimize()
    solver.set("timeout", 3000)
    result = []
    if model.func_obj is not None:
        impact = model.func_obj
        obj = Abs(impact - impact)
        solver.minimize(obj)
    solver.add(model.domain)
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
