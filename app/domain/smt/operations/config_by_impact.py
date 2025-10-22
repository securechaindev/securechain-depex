from z3 import Abs, Optimize, sat, unknown

from app.domain.smt.config_sanitizer import ConfigSanitizer
from app.domain.smt.model import SMTModel
from app.exceptions import SMTTimeoutException


class ConfigByImpactOperation:
    @staticmethod
    async def execute(model: SMTModel, impact: int) -> list[dict[str, float | int]]:
        solver = Optimize()
        solver.set("timeout", 3000)
        result = []
        if model.func_obj is not None:
            impact_obj = model.func_obj
            obj = Abs(impact - impact_obj)
            solver.minimize(obj)
        solver.add(model.domain)
        if solver.check() == sat:
            config = solver.model()
            sanitized_config = await ConfigSanitizer.sanitize(model.node_type, config)
            result.append(sanitized_config)
        elif solver.check() == unknown:
            raise SMTTimeoutException()
        return result
