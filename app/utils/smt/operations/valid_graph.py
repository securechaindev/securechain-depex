from fastapi import status
from fastapi.responses import JSONResponse
from z3 import Solver, sat, unknown

from app.exceptions import SMTTimeoutException
from app.utils import json_encoder
from app.utils.smt.model import SMTModel


async def execute_valid_graph(model: SMTModel) -> JSONResponse:
    solver = Solver()
    solver.set("timeout", 3000)
    solver.add(model.domain)
    if solver.check() == unknown:
        raise SMTTimeoutException()
    else:
        result = solver.check() == sat
    return JSONResponse(
        status_code=status.HTTP_200_OK, content= await json_encoder(
            {
                "result": result,
                "detail": "operation_success",
            }
        )
    )
