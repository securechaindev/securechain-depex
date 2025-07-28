from z3 import Optimize, Or, sat, unknown

from app.utils.smt.config_sanitizer import config_sanitizer
from app.utils.smt.model import SMTModel


async def execute_maximize_impact(model: SMTModel, limit: int) -> list[dict[str, float | int]] | str:
    solver = Optimize()
    solver.set("timeout", 3000)
    result = []
    if model.func_obj is not None:
        impact = model.func_obj
        solver.maximize(impact)
    solver.add(model.domain)
    while len(result) < limit and solver.check() == sat:
        config = solver.model()
        sanitized_config = await config_sanitizer(model.node_type, config)
        result.append(sanitized_config)
        block = []
        for var in config:
            if str(var) != "/0":
                variable = var()
                if "CVSS" not in str(variable):
                    block.append(config[var] != variable)
        solver.add(Or(block))
    if solver.check() == unknown:
        result = (
            "Execution timed out after 3 seconds. The complexity of the model is too high, try lowering the maximum level of the graph."
        )
    return result
