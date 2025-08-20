from fastapi import status
from fastapi.responses import JSONResponse
from z3 import Int, Optimize, sat, unknown

from app.exceptions import SMTTimeoutException
from app.utils import json_encoder
from app.utils.smt.config_sanitizer import config_sanitizer
from app.utils.smt.model import SMTModel


async def execute_complete_config(model: SMTModel, config: dict[str, int]) -> JSONResponse:
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
        sanitized_config = await config_sanitizer(model.node_type, config)
        result.append(sanitized_config)
    elif solver.check() == unknown:
        raise SMTTimeoutException()
    return JSONResponse(
        status_code=status.HTTP_200_OK, content=json_encoder(
            {
                "result": result,
                "detail": "operation_success",
            }
        )
    )
