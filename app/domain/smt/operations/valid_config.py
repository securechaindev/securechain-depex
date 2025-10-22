from z3 import Int, Solver, sat, unknown

from app.domain.smt.model import SMTModel
from app.exceptions import SMTTimeoutException


class ValidConfigOperation:
    @staticmethod
    async def execute(model: SMTModel, config: dict[str, int]) -> bool:
        solver = Solver()
        solver.set("timeout", 3000)
        solver.add(model.domain)
        for package, serial_number in config.items():
            solver.add(Int(package) == serial_number)
        if solver.check() == unknown:
            raise SMTTimeoutException()
        return solver.check() == sat
