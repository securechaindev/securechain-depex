from z3 import Optimize, Or, sat, unknown

from app.domain.smt.config_sanitizer import ConfigSanitizer
from app.domain.smt.model import SMTModel
from app.exceptions import SMTTimeoutException
from app.settings import settings


class MaximizeImpactOperation:
    @staticmethod
    async def execute(model: SMTModel, limit: int) -> list[dict[str, float | int]]:
        solver = Optimize()
        solver.set("timeout", settings.SMT_SOLVER_TIMEOUT_MS)
        result = []
        config_sanitizer = ConfigSanitizer()
        if model.func_obj is not None:
            impact = model.func_obj
            solver.maximize(impact)
        solver.add(model.domain)
        while len(result) < limit and solver.check() == sat:
            config = solver.model()
            sanitized_config = await config_sanitizer.sanitize(model.node_type, config)
            result.append(sanitized_config)
            block = []
            for var in config:
                if str(var) != "/0":
                    variable = var()
                    if "CVSS" not in str(variable):
                        block.append(config[var] != variable)
            solver.add(Or(block))
        if solver.check() == unknown:
            raise SMTTimeoutException()
        return result
