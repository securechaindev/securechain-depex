from z3 import Int, Solver, sat, unknown

from app.domain.smt.model import SMTModel
from app.exceptions import SMTTimeoutException
from app.settings import settings


class ValidConfigOperation:
    @staticmethod
    def execute(model: SMTModel, config: dict[str, int]) -> bool:
        solver = Solver()
        solver.set("timeout", settings.SMT_SOLVER_TIMEOUT_MS)
        solver.add(model.domain)
        for package, serial_number in config.items():
            solver.add(Int(package) == serial_number)
        if solver.check() == unknown:
            raise SMTTimeoutException()
        return solver.check() == sat
