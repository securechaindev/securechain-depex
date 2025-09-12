from typing import Annotated

from fastapi import APIRouter, Body, Depends, Request, status
from fastapi.responses import JSONResponse

from app.limiter import limiter
from app.schemas import PackageInfoRequest, VersionInfoRequest
from app.services import (
    read_graph_for_package_ssc_info_operation,
    read_graph_for_version_ssc_info_operation,
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
    "/operation/ssc/package_ssc_info",
    summary="Get Package SSC Information",
    description="Retrieve information about the software supply chain of a specific package.",
    response_description="SSC package information.",
    dependencies=[Depends(JWTBearer())],
    tags=["Secure Chain Depex - Operation/SSC"]
)
@limiter.limit("5/minute")
async def package_ssc_info(
    request: Request,
    package_info_request: Annotated[PackageInfoRequest, Body()]
) -> JSONResponse:
    operation_result_id = f"{package_info_request.node_type.value}:{package_info_request.package_name}:{package_info_request.max_depth}"
    operation_result = await read_operation_result(operation_result_id)
    if operation_result is not None:
        result = operation_result["result"]
    else:
        result = await read_graph_for_package_ssc_info_operation(
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


@router.post(
    "/operation/ssc/version_ssc_info",
    summary="Get Package Version SSC Information",
    description="Retrieve information about the software supply chain of a specific package version.",
    response_description="SSC package version information.",
    dependencies=[Depends(JWTBearer())],
    tags=["Secure Chain Depex - Operation/SSC"]
)
@limiter.limit("5/minute")
async def version_ssc_info(
    request: Request,
    version_info_request: Annotated[VersionInfoRequest, Body()]
) -> JSONResponse:
    operation_result_id = f"{version_info_request.node_type.value}:{version_info_request.package_name}:{version_info_request.version_name}:{version_info_request.max_depth}"
    operation_result = await read_operation_result(operation_result_id)
    if operation_result is not None:
        result = operation_result["result"]
    else:
        result = await read_graph_for_version_ssc_info_operation(
            version_info_request.node_type.value,
            version_info_request.package_name,
            version_info_request.version_name,
            version_info_request.max_depth
        )
        if result["total_direct_dependencies"] != 0:
            for direct_package in result["direct_dependencies"]:
                direct_package["versions"] = await filter_versions(
                    version_info_request.node_type.value,
                    direct_package["versions"],
                    direct_package["package_constraints"]
                )
            for _, indirect_packages in result["indirect_dependencies_by_depth"].items():
                for indirect_package in indirect_packages:
                    indirect_package["versions"] = await filter_versions(
                        version_info_request.node_type.value,
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
