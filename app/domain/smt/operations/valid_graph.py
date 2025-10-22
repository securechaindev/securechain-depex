from z3 import Solver, sat, unknown

from app.domain.smt.model import SMTModel
from app.exceptions import SMTTimeoutException


class ValidGraphOperation:
    @staticmethod
    async def execute(model: SMTModel) -> bool:
        solver = Solver()
        solver.set("timeout", 3000)
        solver.add(model.domain)
        if solver.check() == unknown:
            raise SMTTimeoutException()
        return solver.check() == sat
