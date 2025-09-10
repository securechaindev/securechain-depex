from typing import Annotated

from fastapi import APIRouter, Body, Depends, Request, status
from fastapi.responses import JSONResponse

from app.limiter import limiter
from app.schemas import PackageInfoRequest
from app.services import (
    read_graph_for_package_info_operation,
    read_operation_result,
    replace_operation_result,
)
from app.utils import (
    JWTBearer,
    filter_versions,
    json_encoder,
)

router = APIRouter()

@router.post(
    "/operation/package/package_info",
    summary="Get Package Information",
    description="Retrieve information about dependnecy graph of a specific package.",
    response_description="Package information.",
    dependencies=[Depends(JWTBearer())],
    tags=["Secure Chain Depex - Operation/Package"]
)
@limiter.limit("5/minute")
async def package_info(
    request: Request,
    package_info_request: Annotated[PackageInfoRequest, Body()]
) -> JSONResponse:
    operation_result_id = f"{package_info_request.node_type.value}:{package_info_request.package_name}:{package_info_request.max_depth}"
    operation_result = await read_operation_result(operation_result_id)
    if operation_result is not None:
        result = operation_result["result"]
    else:
        result = await read_graph_for_package_info_operation(
            package_info_request.node_type.value,
            package_info_request.package_name,
            package_info_request.max_depth
        )
        if result["total_direct_dependencies"] != 0:
            for direct_package in result["direct_dependencies"]:
                direct_package["versions"] = await filter_versions(
                    package_info_request.node_type.value,
                    direct_package["versions"],
                    direct_package["package_constraints"]
                )
            for _, indirect_packages in result["indirect_dependencies_by_depth"].items():
                for indirect_package in indirect_packages:
                    indirect_package["versions"] = await filter_versions(
                        package_info_request.node_type.value,
                        indirect_package["versions"],
                        indirect_package["package_constraints"]
                    )
        else:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content= await json_encoder(
                    {
                        "detail": "no_dependencies",
                    }
                ),
            )
        await replace_operation_result(operation_result_id, result)
    return JSONResponse(
        status_code=status.HTTP_200_OK, content= await json_encoder(
            {
                "result": result,
                "detail": "file_info_success",
            }
        )
    )

