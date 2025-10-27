from z3 import And, AstVector, Or, Solver, sat, unknown

from app.domain.smt.config_sanitizer import ConfigSanitizer
from app.domain.smt.model import SMTModel
from app.exceptions import SMTTimeoutException
from app.settings import settings


class FilterConfigsOperation:
    @staticmethod
    async def execute(
        model: SMTModel, max_threshold: float, min_threshold: float, limit: int
    ) -> list[dict[str, float | int]]:
        if model.func_obj is not None:
            impact = model.func_obj
            max_ctc = impact <= max_threshold
            min_ctc = impact >= min_threshold
        solver = Solver()
        result = []
        config_sanitizer = ConfigSanitizer()
        solver.set("timeout", settings.SMT_SOLVER_TIMEOUT_MS)
        domain_parts = (
            list(model.domain) if isinstance(model.domain, AstVector) else [model.domain]
        )
        expr = And([*domain_parts, max_ctc, min_ctc])
        solver.add(expr)
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
