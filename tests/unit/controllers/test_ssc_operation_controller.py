from datetime import datetime
from json import loads
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytz
from fastapi import Request, status

from app.controllers.ssc_operation_controller import (
    package_ssc_info,
    requirement_file_info,
    version_ssc_info,
)
from app.schemas.enums import NodeType


class TestSSCOperationController:
    @pytest.fixture
    def mock_request(self):
        request = MagicMock(spec=Request)
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        return request

    @pytest.fixture
    def mock_json_encoder(self):
        encoder = MagicMock()
        encoder.encode = MagicMock(side_effect=lambda x: x)
        return encoder

    @pytest.fixture
    def mock_requirement_file_service(self):
        return AsyncMock()

    @pytest.fixture
    def mock_package_service(self):
        return AsyncMock()

    @pytest.fixture
    def mock_version_service(self):
        return AsyncMock()

    @pytest.fixture
    def mock_operation_service(self):
        return AsyncMock()

    @pytest.mark.asyncio
    @patch("app.controllers.ssc_operation_controller.limiter")
    @patch("app.controllers.ssc_operation_controller.VersionFilter")
    async def test_requirement_file_info_with_cache(
        self, _mock_version_filter, _mock_limiter, mock_request,
        mock_requirement_file_service, mock_operation_service, mock_json_encoder
    ):
        cached_result = {
            "total_direct_dependencies": 2,
            "direct_dependencies": [],
            "indirect_dependencies_by_depth": {}
        }
        mock_operation_service.read_operation_result.return_value = {
            "result": cached_result,
            "moment": datetime(2023, 12, 1, tzinfo=pytz.UTC)
        }
        mock_requirement_file_service.read_requirement_file_moment.return_value = datetime(2023, 11, 1, tzinfo=pytz.UTC)

        file_info_request = MagicMock()
        file_info_request.node_type = NodeType.pypi_package
        file_info_request.requirement_file_id = "req-123"
        file_info_request.max_depth = 2

        response = await requirement_file_info(
            mock_request,
            file_info_request,
            mock_requirement_file_service,
            mock_operation_service,
            mock_json_encoder
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = loads(response.body)
        assert response_data["result"] == cached_result
        response_data = loads(response.body)
        assert response_data["code"] == "file_info_success"
        mock_operation_service.replace_operation_result.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.controllers.ssc_operation_controller.limiter")
    @patch("app.controllers.ssc_operation_controller.VersionFilter")
    async def test_requirement_file_info_compute_with_dependencies(
        self, mock_version_filter, _mock_limiter, mock_request,
        mock_requirement_file_service, mock_operation_service, mock_json_encoder
    ):
        mock_operation_service.read_operation_result.return_value = None
        mock_requirement_file_service.read_requirement_file_moment.return_value = datetime(2023, 11, 1, tzinfo=pytz.UTC)

        computed_result = {
            "total_direct_dependencies": 1,
            "direct_dependencies": [
                {
                    "package_name": "requests",
                    "package_constraints": ">=2.0.0",
                    "versions": [{"version": "2.28.0"}]
                }
            ],
            "indirect_dependencies_by_depth": {
                "1": [
                    {
                        "package_name": "urllib3",
                        "package_constraints": "",
                        "versions": [{"version": "1.26.0"}]
                    }
                ]
            }
        }
        mock_requirement_file_service.read_graph_for_req_file_ssc_info_operation.return_value = computed_result
        mock_version_filter.filter_versions.return_value = [{"version": "2.28.0"}]

        file_info_request = MagicMock()
        file_info_request.node_type = NodeType.pypi_package
        file_info_request.requirement_file_id = "req-123"
        file_info_request.max_depth = 2

        response = await requirement_file_info(
            mock_request,
            file_info_request,
            mock_requirement_file_service,
            mock_operation_service,
            mock_json_encoder
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = loads(response.body)
        assert response_data["result"]["total_direct_dependencies"] == 1
        mock_operation_service.replace_operation_result.assert_called_once()
        assert mock_version_filter.filter_versions.call_count == 2

    @pytest.mark.asyncio
    @patch("app.controllers.ssc_operation_controller.limiter")
    @patch("app.controllers.ssc_operation_controller.VersionFilter")
    async def test_requirement_file_info_no_dependencies(
        self, _mock_version_filter, _mock_limiter, mock_request,
        mock_requirement_file_service, mock_operation_service, mock_json_encoder
    ):
        mock_operation_service.read_operation_result.return_value = None
        mock_requirement_file_service.read_requirement_file_moment.return_value = datetime(2023, 11, 1, tzinfo=pytz.UTC)
        mock_requirement_file_service.read_graph_for_req_file_ssc_info_operation.return_value = {
            "total_direct_dependencies": 0,
            "direct_dependencies": [],
            "indirect_dependencies_by_depth": {}
        }

        file_info_request = MagicMock()
        file_info_request.node_type = NodeType.pypi_package
        file_info_request.requirement_file_id = "req-123"
        file_info_request.max_depth = 2

        response = await requirement_file_info(
            mock_request,
            file_info_request,
            mock_requirement_file_service,
            mock_operation_service,
            mock_json_encoder
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = loads(response.body)
        assert response_data["code"] == "no_dependencies_req_file"
        mock_operation_service.replace_operation_result.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.controllers.ssc_operation_controller.limiter")
    @patch("app.controllers.ssc_operation_controller.VersionFilter")
    async def test_package_ssc_info_with_cache(
        self, _mock_version_filter, _mock_limiter, mock_request,
        mock_package_service, mock_operation_service, mock_json_encoder
    ):
        cached_result = {
            "total_direct_dependencies": 3,
            "direct_dependencies": [],
            "indirect_dependencies_by_depth": {}
        }
        mock_operation_service.read_operation_result.return_value = {
            "result": cached_result
        }

        package_info_request = MagicMock()
        package_info_request.node_type = NodeType.npm_package
        package_info_request.package_name = "express"
        package_info_request.max_depth = 3

        response = await package_ssc_info(
            mock_request,
            package_info_request,
            mock_package_service,
            mock_operation_service,
            mock_json_encoder
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = loads(response.body)
        assert response_data["result"] == cached_result
        mock_operation_service.replace_operation_result.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.controllers.ssc_operation_controller.limiter")
    @patch("app.controllers.ssc_operation_controller.VersionFilter")
    async def test_package_ssc_info_compute_with_dependencies(
        self, mock_version_filter, _mock_limiter, mock_request,
        mock_package_service, mock_operation_service, mock_json_encoder
    ):
        mock_operation_service.read_operation_result.return_value = None

        computed_result = {
            "total_direct_dependencies": 2,
            "direct_dependencies": [
                {
                    "package_name": "lodash",
                    "package_constraints": "^4.0.0",
                    "versions": [{"version": "4.17.21"}]
                }
            ],
            "indirect_dependencies_by_depth": {}
        }
        mock_package_service.read_graph_for_package_ssc_info_operation.return_value = computed_result
        mock_version_filter.filter_versions.return_value = [{"version": "4.17.21"}]

        package_info_request = MagicMock()
        package_info_request.node_type = NodeType.npm_package
        package_info_request.package_name = "express"
        package_info_request.max_depth = 3

        response = await package_ssc_info(
            mock_request,
            package_info_request,
            mock_package_service,
            mock_operation_service,
            mock_json_encoder
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = loads(response.body)
        assert response_data["result"]["total_direct_dependencies"] == 2
        mock_operation_service.replace_operation_result.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.controllers.ssc_operation_controller.limiter")
    @patch("app.controllers.ssc_operation_controller.VersionFilter")
    async def test_package_ssc_info_no_dependencies(
        self, _mock_version_filter, _mock_limiter, mock_request,
        mock_package_service, mock_operation_service, mock_json_encoder
    ):
        mock_operation_service.read_operation_result.return_value = None
        mock_package_service.read_graph_for_package_ssc_info_operation.return_value = {
            "total_direct_dependencies": 0,
            "direct_dependencies": [],
            "indirect_dependencies_by_depth": {}
        }

        package_info_request = MagicMock()
        package_info_request.node_type = NodeType.npm_package
        package_info_request.package_name = "empty-package"
        package_info_request.max_depth = 1

        response = await package_ssc_info(
            mock_request,
            package_info_request,
            mock_package_service,
            mock_operation_service,
            mock_json_encoder
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = loads(response.body)
        assert response_data["code"] == "no_dependencies_package"
        mock_operation_service.replace_operation_result.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.controllers.ssc_operation_controller.limiter")
    @patch("app.controllers.ssc_operation_controller.VersionFilter")
    async def test_version_ssc_info_with_cache(
        self, _mock_version_filter, _mock_limiter, mock_request,
        mock_version_service, mock_operation_service, mock_json_encoder
    ):
        cached_result = {
            "total_direct_dependencies": 5,
            "direct_dependencies": [],
            "indirect_dependencies_by_depth": {}
        }
        mock_operation_service.read_operation_result.return_value = {
            "result": cached_result
        }

        version_info_request = MagicMock()
        version_info_request.node_type = NodeType.maven_package
        version_info_request.package_name = "junit"
        version_info_request.version_name = "4.13.2"
        version_info_request.max_depth = 1

        response = await version_ssc_info(
            mock_request,
            version_info_request,
            mock_version_service,
            mock_operation_service,
            mock_json_encoder
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = loads(response.body)
        assert response_data["result"] == cached_result
        mock_operation_service.replace_operation_result.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.controllers.ssc_operation_controller.limiter")
    @patch("app.controllers.ssc_operation_controller.VersionFilter")
    async def test_version_ssc_info_compute_with_dependencies(
        self, mock_version_filter, _mock_limiter, mock_request,
        mock_version_service, mock_operation_service, mock_json_encoder
    ):
        mock_operation_service.read_operation_result.return_value = None

        computed_result = {
            "total_direct_dependencies": 1,
            "direct_dependencies": [
                {
                    "package_name": "hamcrest-core",
                    "package_constraints": "",
                    "versions": [{"version": "1.3"}]
                }
            ],
            "indirect_dependencies_by_depth": {}
        }
        mock_version_service.read_graph_for_version_ssc_info_operation.return_value = computed_result
        mock_version_filter.filter_versions.return_value = [{"version": "1.3"}]

        version_info_request = MagicMock()
        version_info_request.node_type = NodeType.maven_package
        version_info_request.package_name = "junit"
        version_info_request.version_name = "4.13.2"
        version_info_request.max_depth = 1

        response = await version_ssc_info(
            mock_request,
            version_info_request,
            mock_version_service,
            mock_operation_service,
            mock_json_encoder
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = loads(response.body)
        assert response_data["result"]["total_direct_dependencies"] == 1
        mock_operation_service.replace_operation_result.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.controllers.ssc_operation_controller.limiter")
    @patch("app.controllers.ssc_operation_controller.VersionFilter")
    async def test_version_ssc_info_no_dependencies(
        self, _mock_version_filter, _mock_limiter, mock_request,
        mock_version_service, mock_operation_service, mock_json_encoder
    ):
        mock_operation_service.read_operation_result.return_value = None
        mock_version_service.read_graph_for_version_ssc_info_operation.return_value = {
            "total_direct_dependencies": 0,
            "direct_dependencies": [],
            "indirect_dependencies_by_depth": {}
        }

        version_info_request = MagicMock()
        version_info_request.node_type = NodeType.maven_package
        version_info_request.package_name = "standalone-lib"
        version_info_request.version_name = "1.0.0"
        version_info_request.max_depth = 1

        response = await version_ssc_info(
            mock_request,
            version_info_request,
            mock_version_service,
            mock_operation_service,
            mock_json_encoder
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = loads(response.body)
        assert response_data["code"] == "no_dependencies_version"
        mock_operation_service.replace_operation_result.assert_not_called()
