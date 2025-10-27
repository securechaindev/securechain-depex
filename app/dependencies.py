from __future__ import annotations

from app.apis import GitHubService
from app.database import DatabaseManager
from app.http_session import HTTPSessionManager
from app.logger import LoggerManager
from app.services import (
    OperationService,
    PackageService,
    RepositoryService,
    RequirementFileService,
    SMTService,
    VersionService,
)
from app.utils import JSONEncoder, JWTBearer, RedisQueue


class ServiceContainer:
    instance: ServiceContainer | None = None
    db_manager: DatabaseManager | None = None
    repository_service: RepositoryService | None = None
    requirement_file_service: RequirementFileService | None = None
    package_service: PackageService | None = None
    version_service: VersionService | None = None
    smt_service: SMTService | None = None
    operation_service: OperationService | None = None
    github_service: GitHubService | None = None
    redis_queue: RedisQueue | None = None
    json_encoder: JSONEncoder | None = None
    jwt_bearer: JWTBearer | None = None
    logger: LoggerManager | None = None
    http_session: HTTPSessionManager | None = None

    def __new__(cls) -> ServiceContainer:
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    def get_db(self) -> DatabaseManager:
        if self.db_manager is None:
            self.db_manager = DatabaseManager()
        return self.db_manager

    def get_repository_service(self) -> RepositoryService:
        if self.repository_service is None:
            self.repository_service = RepositoryService(self.get_db())
        return self.repository_service

    def get_requirement_file_service(self) -> RequirementFileService:
        if self.requirement_file_service is None:
            self.requirement_file_service = RequirementFileService(self.get_db())
        return self.requirement_file_service

    def get_package_service(self) -> PackageService:
        if self.package_service is None:
            self.package_service = PackageService(self.get_db())
        return self.package_service

    def get_version_service(self) -> VersionService:
        if self.version_service is None:
            self.version_service = VersionService(self.get_db())
        return self.version_service

    def get_smt_service(self) -> SMTService:
        if self.smt_service is None:
            self.smt_service = SMTService(self.get_db())
        return self.smt_service

    def get_operation_service(self) -> OperationService:
        if self.operation_service is None:
            self.operation_service = OperationService(self.get_db())
        return self.operation_service

    def get_github_service(self) -> GitHubService:
        if self.github_service is None:
            self.github_service = GitHubService(self.get_http_session())
        return self.github_service

    def get_redis_queue(self) -> RedisQueue:
        if self.redis_queue is None:
            self.redis_queue = RedisQueue.from_env()
        return self.redis_queue

    def get_json_encoder(self) -> JSONEncoder:
        if self.json_encoder is None:
            self.json_encoder = JSONEncoder()
        return self.json_encoder

    def get_jwt_bearer(self) -> JWTBearer:
        if self.jwt_bearer is None:
            self.jwt_bearer = JWTBearer()
        return self.jwt_bearer

    def get_logger(self) -> LoggerManager:
        if self.logger is None:
            self.logger = LoggerManager()
        return self.logger

    def get_http_session(self) -> HTTPSessionManager:
        if self.http_session is None:
            self.http_session = HTTPSessionManager()
        return self.http_session


def get_db() -> DatabaseManager:
    return ServiceContainer().get_db()


def get_repository_service() -> RepositoryService:
    return ServiceContainer().get_repository_service()


def get_requirement_file_service() -> RequirementFileService:
    return ServiceContainer().get_requirement_file_service()


def get_package_service() -> PackageService:
    return ServiceContainer().get_package_service()


def get_version_service() -> VersionService:
    return ServiceContainer().get_version_service()


def get_smt_service() -> SMTService:
    return ServiceContainer().get_smt_service()


def get_operation_service() -> OperationService:
    return ServiceContainer().get_operation_service()


def get_github_service() -> GitHubService:
    return ServiceContainer().get_github_service()


def get_redis_queue() -> RedisQueue:
    return ServiceContainer().get_redis_queue()


def get_json_encoder() -> JSONEncoder:
    return ServiceContainer().get_json_encoder()


def get_jwt_bearer() -> JWTBearer:
    return ServiceContainer().get_jwt_bearer()


def get_logger() -> LoggerManager:
    return ServiceContainer().get_logger()


def get_http_session() -> HTTPSessionManager:
    return ServiceContainer().get_http_session()
