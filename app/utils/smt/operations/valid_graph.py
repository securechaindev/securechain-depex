from z3 import Solver, sat, unknown

from fastapi import status
from fastapi.responses import JSONResponse

from app.utils.smt.model import SMTModel
from app.utils import json_encoder


async def execute_valid_graph(model: SMTModel) -> JSONResponse:
    solver = Solver()
    solver.set("timeout", 3000)
    solver.add(model.domain)
    if solver.check() == unknown:
        result = ""
        code = "smt_timeout"
    else:
        result = solver.check() == sat
        code = "operation_success"
    return JSONResponse(
        status_code=status.HTTP_200_OK, content=json_encoder(
            {
                "result": result,
                "code": code,
            }
        )
    )
