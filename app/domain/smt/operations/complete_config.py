from z3 import Int, Optimize, sat, unknown

from app.domain.smt.config_sanitizer import ConfigSanitizer
from app.domain.smt.model import SMTModel
from app.exceptions import SMTTimeoutException


class CompleteConfigOperation:
    @staticmethod
    async def execute(
        model: SMTModel, config: dict[str, int]
    ) -> list[dict[str, float | int]]:
        solver = Optimize()
        solver.set("timeout", 3000)
        result = []
        if model.func_obj is not None:
            impact = model.func_obj
            solver.minimize(impact)
        solver.add(model.domain)
        for package, serial_number in config.items():
            solver.add(Int(package) == serial_number)
        if solver.check() == sat:
            config = solver.model()
            sanitized_config = await ConfigSanitizer.sanitize(model.node_type, config)
            result.append(sanitized_config)
        elif solver.check() == unknown:
            raise SMTTimeoutException()
        return result
