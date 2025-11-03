from datetime import datetime
from json import loads
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytz
from fastapi import Request, status

from app.controllers.smt_operation_controller import (
    complete_config,
    config_by_impact,
    filter_configs,
    maximize_impact,
    minimize_impact,
    valid_config,
    valid_graph,
)
from app.schemas.enums import NodeType


class TestSMTOperationController:
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
    def mock_version_service(self):
        return AsyncMock()

    @pytest.fixture
    def mock_smt_service(self):
        return AsyncMock()

    @pytest.mark.asyncio
    @patch("app.controllers.smt_operation_controller.limiter")
    async def test_valid_graph_no_dependencies(
        self, _mock_limiter, mock_request,
        mock_requirement_file_service, mock_smt_service, mock_json_encoder
    ):
        mock_requirement_file_service.read_data_for_smt_transform.return_value = {
            "name": None,
            "moment": datetime(2023, 11, 1, tzinfo=pytz.UTC)
        }

        valid_graph_request = MagicMock()
        valid_graph_request.requirement_file_id = "req-123"
        valid_graph_request.max_depth = 2
        valid_graph_request.node_type = NodeType.pypi_package

        response = await valid_graph(
            mock_request,
            valid_graph_request,
            mock_requirement_file_service,
            mock_smt_service,
            mock_json_encoder
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = loads(response.body)
        assert response_data["code"] == "no_dependencies"

    @pytest.mark.asyncio
    @patch("app.controllers.smt_operation_controller.limiter")
    async def test_minimize_impact_no_dependencies(
        self, _mock_limiter, mock_request,
        mock_requirement_file_service, mock_smt_service, mock_json_encoder
    ):
        mock_requirement_file_service.read_data_for_smt_transform.return_value = {
            "name": None,
            "moment": datetime(2023, 11, 1, tzinfo=pytz.UTC)
        }

        min_max_impact_request = MagicMock()
        min_max_impact_request.requirement_file_id = "req-123"
        min_max_impact_request.max_depth = 2
        min_max_impact_request.node_type = NodeType.pypi_package
        min_max_impact_request.limit = 10

        response = await minimize_impact(
            mock_request,
            min_max_impact_request,
            mock_requirement_file_service,
            mock_smt_service,
            mock_json_encoder
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = loads(response.body)
        assert response_data["code"] == "no_dependencies"

    @pytest.mark.asyncio
    @patch("app.controllers.smt_operation_controller.limiter")
    async def test_maximize_impact_no_dependencies(
        self, _mock_limiter, mock_request,
        mock_requirement_file_service, mock_smt_service, mock_json_encoder
    ):
        mock_requirement_file_service.read_data_for_smt_transform.return_value = {
            "name": None,
            "moment": datetime(2023, 11, 1, tzinfo=pytz.UTC)
        }

        min_max_impact_request = MagicMock()
        min_max_impact_request.requirement_file_id = "req-123"
        min_max_impact_request.max_depth = 2
        min_max_impact_request.node_type = NodeType.npm_package
        min_max_impact_request.limit = 5

        response = await maximize_impact(
            mock_request,
            min_max_impact_request,
            mock_requirement_file_service,
            mock_smt_service,
            mock_json_encoder
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = loads(response.body)
        assert response_data["code"] == "no_dependencies"

    @pytest.mark.asyncio
    @patch("app.controllers.smt_operation_controller.limiter")
    async def test_filter_configs_no_dependencies(
        self, _mock_limiter, mock_request,
        mock_requirement_file_service, mock_smt_service, mock_json_encoder
    ):
        mock_requirement_file_service.read_data_for_smt_transform.return_value = {
            "name": None,
            "moment": datetime(2023, 11, 1, tzinfo=pytz.UTC)
        }

        filter_configs_request = MagicMock()
        filter_configs_request.requirement_file_id = "req-123"
        filter_configs_request.max_depth = 3
        filter_configs_request.node_type = NodeType.maven_package
        filter_configs_request.min_impact = 1.0
        filter_configs_request.max_impact = 10.0

        response = await filter_configs(
            mock_request,
            filter_configs_request,
            mock_requirement_file_service,
            mock_smt_service,
            mock_json_encoder
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = loads(response.body)
        assert response_data["code"] == "no_dependencies"

    @pytest.mark.asyncio
    @patch("app.controllers.smt_operation_controller.limiter")
    async def test_valid_config_no_dependencies(
        self, _mock_limiter, mock_request,
        mock_requirement_file_service, mock_version_service, mock_smt_service, mock_json_encoder
    ):
        mock_requirement_file_service.read_data_for_smt_transform.return_value = {
            "name": None,
            "moment": datetime(2023, 11, 1, tzinfo=pytz.UTC)
        }

        valid_config_request = MagicMock()
        valid_config_request.requirement_file_id = "req-123"
        valid_config_request.max_depth = 2
        valid_config_request.node_type = NodeType.rubygems_package
        valid_config_request.config = {"package1": "1.0.0"}

        response = await valid_config(
            mock_request,
            valid_config_request,
            mock_requirement_file_service,
            mock_version_service,
            mock_smt_service,
            mock_json_encoder
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = loads(response.body)
        assert response_data["code"] == "no_dependencies"

    @pytest.mark.asyncio
    @patch("app.controllers.smt_operation_controller.limiter")
    async def test_complete_config_no_dependencies(
        self, _mock_limiter, mock_request,
        mock_requirement_file_service, mock_version_service, mock_smt_service, mock_json_encoder
    ):
        mock_requirement_file_service.read_data_for_smt_transform.return_value = {
            "name": None,
            "moment": datetime(2023, 11, 1, tzinfo=pytz.UTC)
        }

        complete_config_request = MagicMock()
        complete_config_request.requirement_file_id = "req-123"
        complete_config_request.max_depth = 1
        complete_config_request.node_type = NodeType.cargo_package
        complete_config_request.config = {}

        response = await complete_config(
            mock_request,
            complete_config_request,
            mock_requirement_file_service,
            mock_version_service,
            mock_smt_service,
            mock_json_encoder
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = loads(response.body)
        assert response_data["code"] == "no_dependencies"

    @pytest.mark.asyncio
    @patch("app.controllers.smt_operation_controller.limiter")
    async def test_config_by_impact_no_dependencies(
        self, _mock_limiter, mock_request,
        mock_requirement_file_service, mock_smt_service, mock_json_encoder
    ):
        mock_requirement_file_service.read_data_for_smt_transform.return_value = {
            "name": None,
            "moment": datetime(2023, 11, 1, tzinfo=pytz.UTC)
        }

        config_by_impact_request = MagicMock()
        config_by_impact_request.requirement_file_id = "req-123"
        config_by_impact_request.max_depth = 2
        config_by_impact_request.node_type = NodeType.nuget_package
        config_by_impact_request.impact = 5.0

        response = await config_by_impact(
            mock_request,
            config_by_impact_request,
            mock_requirement_file_service,
            mock_smt_service,
            mock_json_encoder
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = loads(response.body)
        assert response_data["code"] == "no_dependencies"
