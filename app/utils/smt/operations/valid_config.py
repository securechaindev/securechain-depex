from fastapi import status
from fastapi.responses import JSONResponse
from z3 import Int, Solver, sat, unknown

from app.exceptions import SMTTimeoutException
from app.utils import json_encoder
from app.utils.smt.model import SMTModel


async def execute_valid_config(model: SMTModel, config: dict[str, int]) -> JSONResponse:
    solver = Solver()
    solver.set("timeout", 3000)
    result = []
    solver.add(model.domain)
    for package, serial_number in config.items():
        solver.add(Int(package) == serial_number)
    if solver.check() == unknown:
        raise SMTTimeoutException()
    else:
        result = solver.check() == sat
    return JSONResponse(
        status_code=status.HTTP_200_OK, content=json_encoder(
            {
                "result": result,
                "code": "operation_success",
            }
        )
    )
