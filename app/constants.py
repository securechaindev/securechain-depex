from typing import ClassVar


class FileTypes:
    PYPI: ClassVar[list[str]] = ["pyproject.toml", "setup.cfg", "setup.py", "requirements.txt"]
    NPM: ClassVar[list[str]] = ["package.json", "package-lock.json"]
    MAVEN: ClassVar[list[str]] = ["pom.xml"]
    NUGET: ClassVar[list[str]] = ["packages.config"]
    RUBY: ClassVar[list[str]] = ["Gemfile", "Gemfile.lock"]
    CARGO: ClassVar[list[str]] = ["Cargo.toml", "Cargo.lock"]

    ALL_REQUIREMENT_FILES: ClassVar[set[str]] = set(
        PYPI + NPM + MAVEN + NUGET + RUBY + CARGO
    )

class ResponseCode:
    # Health
    HEALTHY = "healthy"

    # Success operations
    OPERATION_SUCCESS = "operation_success"
    FILE_INFO_SUCCESS = "file_info_success"
    PACKAGE_INFO_SUCCESS = "package_info_success"
    VERSION_INFO_SUCCESS = "version_info_success"
    GET_REPOSITORIES_SUCCESS = "get_repositories_success"
    GET_PACKAGE_STATUS_SUCCESS = "get_package_status_success"
    GET_VERSION_STATUS_SUCCESS = "get_version_status_success"

    # Queue operations
    PACKAGE_QUEUED_FOR_PROCESSING = "package_queued_for_processing"
    REPOSITORY_QUEUED_FOR_PROCESSING = "repository_queued_for_processing"

    # Info/Warning states
    NO_DEPENDENCIES = "no_dependencies"
    NO_DEPENDENCIES_REQ_FILE = "no_dependencies_req_file"
    NO_DEPENDENCIES_PACKAGE = "no_dependencies_package"
    NO_DEPENDENCIES_VERSION = "no_dependencies_version"
    REPOSITORY_PROCESSING_IN_PROGRESS = "repository_processing_in_progress"

    # Not found errors
    PACKAGE_NOT_FOUND = "package_not_found"
    VERSION_NOT_FOUND = "version_not_found"
    DATE_NOT_FOUND = "date_not_found"
    REPOSITORY_NOT_FOUND = "repository_not_found"

    # Error codes - General
    VALIDATION_ERROR = "validation_error"
    HTTP_ERROR = "http_error"
    INTERNAL_ERROR = "internal_error"

    # Authentication errors
    NOT_AUTHENTICATED = "not_authenticated"
    TOKEN_EXPIRED = "token_expired"
    INVALID_TOKEN = "invalid_token"

    # System errors
    MEMORY_OUT = "memory_out"
    SMT_TIMEOUT = "smt_timeout"


class ResponseMessage:
    # Health
    HEALTHY = "The API is running and healthy"

    # Success operations
    GRAPH_VALIDATION_SUCCESS = "Graph validation completed successfully"
    IMPACT_MINIMIZATION_SUCCESS = "Impact minimization completed successfully"
    IMPACT_MAXIMIZATION_SUCCESS = "Impact maximization completed successfully"
    CONFIG_FILTERING_SUCCESS = "Configuration filtering completed successfully"
    CONFIG_VALIDATION_SUCCESS = "Configuration validation completed successfully"
    CONFIG_COMPLETION_SUCCESS = "Configuration completion completed successfully"
    CONFIG_BY_IMPACT_SUCCESS = "Configuration by impact completed successfully"
    FILE_INFO_SUCCESS = "Requirement file information retrieved successfully"
    PACKAGE_INFO_SUCCESS = "Package information retrieved successfully"
    VERSION_INFO_SUCCESS = "Package version information retrieved successfully"
    REPOSITORIES_RETRIEVED_SUCCESS = "Repositories retrieved successfully"
    PACKAGE_STATUS_RETRIEVED_SUCCESS = "Package status retrieved successfully"
    VERSION_STATUS_RETRIEVED_SUCCESS = "Version status retrieved successfully"

    # Queue operations
    PACKAGE_QUEUED = "The package has been queued for processing"
    REPOSITORY_QUEUED = "The repository has been queued for processing"

    # Info/Warning states
    NO_DEPENDENCIES_TO_VALIDATE = "The requirement file has no dependencies to validate"
    NO_DEPENDENCIES_TO_MINIMIZE = "The requirement file has no dependencies to minimize"
    NO_DEPENDENCIES_TO_MAXIMIZE = "The requirement file has no dependencies to maximize"
    NO_DEPENDENCIES_TO_FILTER = "The requirement file has no dependencies to filter"
    NO_DEPENDENCIES_TO_COMPLETE = "The requirement file has no dependencies to complete"
    NO_DEPENDENCIES_TO_PROCESS = "The requirement file has no dependencies to process"
    NO_DEPENDENCIES_REQ_FILE = "The requirement file has no dependencies"
    NO_DEPENDENCIES_PACKAGE = "The package has no dependencies"
    NO_DEPENDENCIES_VERSION = "The package version has no dependencies"
    REPOSITORY_PROCESSING = "The repository is already being processed"

    # Not found errors
    PACKAGE_NOT_FOUND = "The requested package was not found"
    VERSION_NOT_FOUND = "The requested version was not found"

    # Error messages - General
    VALIDATION_ERROR = "Validation error"
    HTTP_ERROR = "HTTP error"
    INTERNAL_ERROR = "Internal server error"

    # Exception messages (with dynamic content)
    DATE_NOT_FOUND = "Last commit date not found in repository {name} for owner {owner}"
    REPOSITORY_NOT_FOUND = "Repository {name} not found for owner {owner}"
    NOT_AUTHENTICATED = "Not authenticated"
    TOKEN_EXPIRED = "Token has expired"
    INVALID_TOKEN = "Invalid token"
    MEMORY_OUT = "Memory exhausted or query timeout"
    SMT_TIMEOUT = "SMT timeout occurred"
