
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.repository_service import RepositoryService


class TestRepositoryService:

    @pytest.fixture
    def mock_db_manager(self):
        db_manager = MagicMock()
        driver = MagicMock()
        db_manager.get_neo4j_driver.return_value = driver
        return db_manager, driver

    @pytest.fixture
    def repository_service(self, mock_db_manager):
        db_manager, _ = mock_db_manager
        return RepositoryService(db_manager)

    async def test_create_repository_success(self, repository_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        result_mock = AsyncMock()
        result_mock.single.return_value = ["repo123"]
        session_mock.run.return_value = result_mock

        repository = {
            "user_id": "user123",
            "owner": "securechaindev",
            "name": "depex",
            "moment": datetime.now(),
            "is_complete": False
        }

        repo_id = await repository_service.create_repository(repository)

        assert repo_id == "repo123"
        session_mock.run.assert_called_once()

    async def test_create_repository_no_record(self, repository_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        result_mock = AsyncMock()
        result_mock.single.return_value = None
        session_mock.run.return_value = result_mock

        repository = {
            "user_id": "nonexistent",
            "owner": "test",
            "name": "test",
            "moment": datetime.now(),
            "is_complete": False
        }

        repo_id = await repository_service.create_repository(repository)

        assert repo_id is None

    async def test_create_user_repository_rel_success(self, repository_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        result_mock = AsyncMock()
        result_mock.single.return_value = {"id": "repo123"}
        session_mock.run.return_value = result_mock

        rel_id = await repository_service.create_user_repository_rel("repo123", "user123")

        assert rel_id == "repo123"
        session_mock.run.assert_called_once()

    async def test_read_repository_by_owner_and_name_found(self, repository_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        result_mock = AsyncMock()
        result_mock.single.return_value = {
            "repository": {
                "id": "repo123",
                "owner": "securechaindev",
                "name": "depex",
                "is_complete": True
            }
        }
        session_mock.run.return_value = result_mock

        repository = await repository_service.read_repository_by_owner_and_name(
            "securechaindev", "depex"
        )

        assert repository["id"] == "repo123"
        assert repository["name"] == "depex"

    async def test_read_repository_by_owner_and_name_not_found(self, repository_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        result_mock = AsyncMock()
        result_mock.single.return_value = None
        session_mock.run.return_value = result_mock

        repository = await repository_service.read_repository_by_owner_and_name(
            "nonexistent", "repo"
        )

        assert repository is None

    async def test_read_repositories_by_user_id_with_repos(self, repository_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        result_mock = AsyncMock()
        result_mock.single.return_value = [
            [
                {
                    "owner": "securechaindev",
                    "name": "depex",
                    "is_complete": True,
                    "requirement_files": [
                        {"name": "requirements.txt", "manager": "pypi", "requirement_file_id": "rf123"}
                    ]
                },
                {
                    "owner": "securechaindev",
                    "name": "other-repo",
                    "is_complete": False,
                    "requirement_files": []
                }
            ]
        ]
        session_mock.run.return_value = result_mock

        repositories = await repository_service.read_repositories_by_user_id("user123")

        assert len(repositories) == 2
        assert repositories[0]["name"] == "depex"
        assert len(repositories[0]["requirement_files"]) == 1

    async def test_read_repositories_by_user_id_no_repos(self, repository_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        result_mock = AsyncMock()
        result_mock.single.return_value = None
        session_mock.run.return_value = result_mock

        repositories = await repository_service.read_repositories_by_user_id("user123")

        assert repositories == []

    async def test_update_repository_is_complete_true(self, repository_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        await repository_service.update_repository_is_complete("repo123", True)

        session_mock.run.assert_called_once()
        call_args = session_mock.run.call_args
        assert call_args[1]["is_complete"] is True

    async def test_update_repository_is_complete_false(self, repository_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        await repository_service.update_repository_is_complete("repo123", False)

        session_mock.run.assert_called_once()
        call_args = session_mock.run.call_args
        assert call_args[1]["is_complete"] is False

    async def test_update_repository_moment(self, repository_service, mock_db_manager):
        _, driver = mock_db_manager
        session_mock = AsyncMock()
        driver.session.return_value.__aenter__.return_value = session_mock

        await repository_service.update_repository_moment("repo123")

        session_mock.run.assert_called_once()
        call_args = session_mock.run.call_args
        assert "moment" in call_args[1]
        assert isinstance(call_args[1]["moment"], datetime)
