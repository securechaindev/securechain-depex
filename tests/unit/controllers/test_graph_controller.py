from json import loads
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request, status

from app.controllers.graph_controller import (
    get_package_status,
    get_repositories,
    get_version_status,
    init_repository,
)
from app.exceptions import InvalidRepositoryException
from app.schemas.enums import NodeType


class TestGraphController:
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
    def mock_repository_service(self):
        return AsyncMock()

    @pytest.fixture
    def mock_package_service(self):
        return AsyncMock()

    @pytest.fixture
    def mock_github_service(self):
        return AsyncMock()

    @pytest.fixture
    def mock_redis_queue(self):
        return MagicMock()

    @pytest.mark.asyncio
    @patch("app.controllers.graph_controller.limiter")
    async def test_get_repositories_success(
        self, _mock_limiter, mock_request, mock_repository_service, mock_json_encoder
    ):
        mock_repos = [
            {"id": "1", "name": "repo1", "owner": "user1"},
            {"id": "2", "name": "repo2", "owner": "user1"}
        ]
        mock_repository_service.read_repositories_by_user_id.return_value = mock_repos

        get_repositories_request = MagicMock()
        get_repositories_request.user_id = "user1"

        response = await get_repositories(
            mock_request,
            get_repositories_request,
            mock_repository_service,
            mock_json_encoder
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = loads(response.body)
        assert response_data["repositories"] == mock_repos
        assert response_data["detail"] == "get_repositories_success"
        mock_repository_service.read_repositories_by_user_id.assert_called_once_with("user1")

    @pytest.mark.asyncio
    @patch("app.controllers.graph_controller.limiter")
    async def test_get_package_status_found(
        self, _mock_limiter, mock_request, mock_package_service, mock_json_encoder
    ):
        mock_package = {"name": "fastapi", "status": "active"}
        mock_package_service.read_package_status_by_name.return_value = mock_package

        get_package_status_request = MagicMock()
        get_package_status_request.node_type = NodeType.pypi_package
        get_package_status_request.package_name = "fastapi"

        response = await get_package_status(
            mock_request,
            get_package_status_request,
            mock_package_service,
            mock_json_encoder
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = loads(response.body)
        assert response_data["package"] == mock_package
        assert response_data["detail"] == "get_package_status_success"
        mock_package_service.read_package_status_by_name.assert_called_once_with(
            NodeType.pypi_package.value, "fastapi"
        )

    @pytest.mark.asyncio
    @patch("app.controllers.graph_controller.limiter")
    async def test_get_package_status_not_found(
        self, _mock_limiter, mock_request, mock_package_service, mock_json_encoder
    ):
        mock_package_service.read_package_status_by_name.return_value = None

        get_package_status_request = MagicMock()
        get_package_status_request.node_type = NodeType.pypi_package
        get_package_status_request.package_name = "nonexistent"

        response = await get_package_status(
            mock_request,
            get_package_status_request,
            mock_package_service,
            mock_json_encoder
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_data = loads(response.body)
        assert "not_found" in response_data["detail"]
        mock_package_service.read_package_status_by_name.assert_called_once_with(
            NodeType.pypi_package.value, "nonexistent"
        )

    @pytest.mark.asyncio
    @patch("app.controllers.graph_controller.limiter")
    async def test_get_version_status_found(
        self, _mock_limiter, mock_request, mock_package_service, mock_json_encoder
    ):
        mock_version = {"version": "1.0.0", "status": "stable"}
        mock_package_service.read_version_status_by_package_and_name.return_value = mock_version

        get_version_status_request = MagicMock()
        get_version_status_request.node_type = NodeType.pypi_package
        get_version_status_request.package_name = "fastapi"
        get_version_status_request.version_name = "1.0.0"

        response = await get_version_status(
            mock_request,
            get_version_status_request,
            mock_package_service,
            mock_json_encoder
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = loads(response.body)
        assert response_data["version"] == mock_version
        assert response_data["detail"] == "get_version_status_success"
        mock_package_service.read_version_status_by_package_and_name.assert_called_once_with(
            NodeType.pypi_package.value, "fastapi", "1.0.0"
        )

    @pytest.mark.asyncio
    @patch("app.controllers.graph_controller.limiter")
    async def test_get_version_status_not_found(
        self, _mock_limiter, mock_request, mock_package_service, mock_json_encoder
    ):
        mock_package_service.read_version_status_by_package_and_name.return_value = None

        get_version_status_request = MagicMock()
        get_version_status_request.node_type = NodeType.pypi_package
        get_version_status_request.package_name = "fastapi"
        get_version_status_request.version_name = "999.0.0"

        response = await get_version_status(
            mock_request,
            get_version_status_request,
            mock_package_service,
            mock_json_encoder
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_data = loads(response.body)
        assert "not_found" in response_data["detail"]
        mock_package_service.read_version_status_by_package_and_name.assert_called_once_with(
            NodeType.pypi_package.value, "fastapi", "999.0.0"
        )

    @pytest.mark.asyncio
    @patch("app.controllers.graph_controller.RepositoryInitializer")
    @patch("app.controllers.graph_controller.limiter")
    async def test_init_repository_success_new_repo(
        self, _mock_limiter, mock_repo_initializer, mock_request, mock_repository_service, mock_github_service, mock_json_encoder
    ):
        mock_github_service.get_last_commit_date.return_value = "2023-01-01"
        mock_repository_service.read_repository_by_owner_and_name.return_value = None

        init_repository_request = MagicMock()
        init_repository_request.owner = "testowner"
        init_repository_request.name = "testrepo"
        init_repository_request.user_id = "user123"

        background_tasks = MagicMock()

        response = await init_repository(
            mock_request,
            init_repository_request,
            background_tasks,
            mock_repository_service,
            mock_github_service,
            mock_json_encoder
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        response_data = loads(response.body)
        assert response_data["detail"] == "repository_queued_for_processing"
        assert "testowner/testrepo" in response_data["repository"]
        mock_github_service.get_last_commit_date.assert_called_once_with("testowner", "testrepo")
        background_tasks.add_task.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.controllers.graph_controller.RepositoryInitializer")
    @patch("app.controllers.graph_controller.limiter")
    async def test_init_repository_success_complete_repo(
        self, _mock_limiter, mock_repo_initializer, mock_request, mock_repository_service, mock_github_service, mock_json_encoder
    ):
        mock_github_service.get_last_commit_date.return_value = "2023-01-01"
        mock_repository_service.read_repository_by_owner_and_name.return_value = {
            "id": "repo123",
            "is_complete": True
        }

        init_repository_request = MagicMock()
        init_repository_request.owner = "testowner"
        init_repository_request.name = "testrepo"
        init_repository_request.user_id = "user123"

        background_tasks = MagicMock()

        response = await init_repository(
            mock_request,
            init_repository_request,
            background_tasks,
            mock_repository_service,
            mock_github_service,
            mock_json_encoder
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        response_data = loads(response.body)
        assert response_data["detail"] == "repository_queued_for_processing"
        background_tasks.add_task.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.controllers.graph_controller.limiter")
    async def test_init_repository_in_progress(
        self, _mock_limiter, mock_request, mock_repository_service, mock_github_service, mock_json_encoder
    ):
        mock_github_service.get_last_commit_date.return_value = "2023-01-01"
        mock_repository_service.read_repository_by_owner_and_name.return_value = {
            "id": "repo123",
            "is_complete": False
        }

        init_repository_request = MagicMock()
        init_repository_request.owner = "testowner"
        init_repository_request.name = "testrepo"
        init_repository_request.user_id = "user123"

        background_tasks = MagicMock()

        response = await init_repository(
            mock_request,
            init_repository_request,
            background_tasks,
            mock_repository_service,
            mock_github_service,
            mock_json_encoder
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        background_tasks.add_task.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.controllers.graph_controller.limiter")
    async def test_init_repository_github_not_found(
        self, _mock_limiter, mock_request, mock_repository_service, mock_github_service, mock_json_encoder
    ):
        mock_github_service.get_last_commit_date.side_effect = InvalidRepositoryException("testowner", "nonexistent")

        init_repository_request = MagicMock()
        init_repository_request.owner = "testowner"
        init_repository_request.name = "nonexistent"
        init_repository_request.user_id = "user123"

        background_tasks = MagicMock()

        response = await init_repository(
            mock_request,
            init_repository_request,
            background_tasks,
            mock_repository_service,
            mock_github_service,
            mock_json_encoder
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        background_tasks.add_task.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.controllers.graph_controller.limiter")
    async def test_init_repository_error(
        self, _mock_limiter, mock_request, mock_repository_service, mock_github_service, mock_json_encoder
    ):
        mock_github_service.get_last_commit_date.side_effect = Exception("Unexpected error")

        init_repository_request = MagicMock()
        init_repository_request.owner = "testowner"
        init_repository_request.name = "testrepo"
        init_repository_request.user_id = "user123"

        background_tasks = MagicMock()

        response = await init_repository(
            mock_request,
            init_repository_request,
            background_tasks,
            mock_repository_service,
            mock_github_service,
            mock_json_encoder
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        background_tasks.add_task.assert_not_called()
