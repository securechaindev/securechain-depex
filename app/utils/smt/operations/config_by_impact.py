from fastapi import status
from fastapi.responses import JSONResponse
from z3 import Abs, Optimize, sat, unknown

from app.utils import json_encoder
from app.utils.smt.config_sanitizer import config_sanitizer
from app.utils.smt.model import SMTModel


async def execute_config_by_impact(model: SMTModel, impact: int) -> JSONResponse:
    solver = Optimize()
    solver.set("timeout", 3000)
    result = []
    if model.func_obj is not None:
        impact = model.func_obj
        obj = Abs(impact - impact)
        solver.minimize(obj)
    solver.add(model.domain)
    if solver.check() == sat:
        config = solver.model()
        sanitized_config = await config_sanitizer(model.node_type, config)
        result.append(sanitized_config)
        code = "operation_success"
    elif solver.check() == unknown:
        result = ""
        code = "smt_timeout"
    return JSONResponse(
        status_code=status.HTTP_200_OK, content=json_encoder(
            {
                "result": result,
                "code": code,
            }
        )
    )
