from fastapi import status
from fastapi.responses import JSONResponse
from z3 import And, Or, Solver, sat, unknown

from app.utils import json_encoder
from app.utils.smt.config_sanitizer import config_sanitizer
from app.utils.smt.model import SMTModel


async def execute_filter_configs(model: SMTModel, max_threshold: float, min_threshold: float, limit: int) -> JSONResponse:
    if model.func_obj is not None:
        impact = model.func_obj
        max_ctc = impact <= max_threshold
        min_ctc = impact >= min_threshold
    solver = Solver()
    result = []
    solver.set("timeout", 3000)
    solver.add(And([model.domain, max_ctc, min_ctc]))
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
