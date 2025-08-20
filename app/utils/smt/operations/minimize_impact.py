from fastapi import status
from fastapi.responses import JSONResponse
from z3 import Optimize, Or, sat, unknown

from app.exceptions import SMTTimeoutException
from app.utils import json_encoder
from app.utils.smt.config_sanitizer import config_sanitizer
from app.utils.smt.model import SMTModel


async def execute_minimize_impact(model: SMTModel, limit: int) -> JSONResponse:
    solver = Optimize()
    solver.set("timeout", 3000)
    result = []
    if model.func_obj is not None:
        impact = model.func_obj
        solver.minimize(impact)
    solver.add(model.domain)
    while len(result) < limit and solver.check() == sat:
        config = solver.model()
        sanitized_config = await config_sanitizer(model.node_type, config)
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
    return JSONResponse(
        status_code=status.HTTP_200_OK, content=json_encoder(
            {
                "result": result,
                "code": "operation_success",
            }
        )
    )
