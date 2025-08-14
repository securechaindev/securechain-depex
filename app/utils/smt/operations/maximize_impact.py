from z3 import Optimize, Or, sat, unknown

from fastapi import status
from fastapi.responses import JSONResponse

from app.utils.smt.config_sanitizer import config_sanitizer
from app.utils.smt.model import SMTModel
from app.utils import json_encoder


async def execute_maximize_impact(model: SMTModel, limit: int) -> JSONResponse:
    solver = Optimize()
    solver.set("timeout", 3000)
    result = []
    if model.func_obj is not None:
        impact = model.func_obj
        solver.maximize(impact)
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
        result = ""
        code = "smt_timeout"
    else:
        code = "operation_success"
    return JSONResponse(
        status_code=status.HTTP_200_OK, content=json_encoder(
            {
                "result": result,
                "code": code,
            }
        )
    )
