# AI Agent Guide - SecureChain DepEx

This document provides contextual information for AI agents working on this project.

## ⚡ Quick Start for AI Agents

If you're an AI agent tasked with working on this project, here's what you need to know immediately:

1. **Project Type:** FastAPI async web application for software supply chain analysis
2. **Python Version:** 3.13+
3. **Package Manager:** uv (not pip or poetry)
4. **Test Coverage:** 84% (target: 90%)
5. **Key Technologies:** FastAPI, MongoDB, Neo4j, Redis, Z3 solver
6. **Testing:** pytest with AsyncMock for services
7. **Code Style:** Ruff for linting/formatting
8. **Important:** All I/O operations are async - never use blocking calls

### Most Common Tasks
- **Run tests:** `uv run pytest --cov=app`
- **Add dependency:** `uv add package-name`
- **Format code:** `uv run ruff format app/`
- **Check linting:** `uv run ruff check app/`

### Critical Patterns to Follow
- Controllers use `@limiter.limit` - always patch in tests with `@patch`
- Response bodies are bytes - use `json.loads(response.body)`
- Services use AsyncMock, simple objects use MagicMock
- Enum values are lowercase with underscores: `NodeType.pypi_package`
- All test classes need fixtures: `mock_request`, `mock_json_encoder`, service mocks

---

## 📋 Project Description

**SecureChain DepEx** is a tool that allows you to reason over the entire configuration space of the Software Supply Chain of an open-source software repository. It's a FastAPI-based API for software dependency analysis and Software Supply Chain (SSC) management. The project analyzes dependency configuration files from multiple languages/ecosystems and performs SMT (Satisfiability Modulo Theories) operations to resolve version constraints.

## 📑 Table of Contents

- [Quick Start for AI Agents](#-quick-start-for-ai-agents)
- [Project Description](#-project-description)
- [Supported Ecosystems](#supported-ecosystems)
- [Project Structure](#️-project-structure)
- [Testing](#-testing)
  - [Current Coverage Status](#current-coverage-status-october-2025)
  - [Testing Conventions](#testing-conventions)
  - [Testing Commands](#testing-commands)
- [Key Concepts](#-key-concepts)
- [Main Dependencies](#-main-dependencies)
- [Known Issues and Solutions](#-known-issues-and-solutions)
- [Code Patterns](#-code-patterns)
- [Areas with Low Coverage](#-areas-with-low-coverage-improvement-opportunities)
- [Development Commands](#-development-commands)
  - [Docker Setup](#docker-setup)
  - [Docker Images Explained](#docker-images-explained)
- [Architecture & Design Decisions](#️-architecture--design-decisions)
- [Common Development Workflows](#-common-development-workflows)
- [Project Metrics & Goals](#-project-metrics--goals)
- [Contributing Guidelines](#-contributing-guidelines)
- [Troubleshooting](#-troubleshooting)
- [Useful References](#-useful-references)
- [Tips for AI Agents](#-tips-for-ai-agents)
- [Contact & Support](#-contact--support)

---

### Key Features
- **Multi-ecosystem support:** Analyzes dependencies from Python, JavaScript, Ruby, Rust, Java, and PHP
- **SMT-based reasoning:** Uses Z3 solver to find optimal dependency configurations
- **Graph-based analysis:** Builds and analyzes dependency graphs using Neo4j
- **Caching layer:** Redis-based caching for improved performance
- **Supply Chain Security:** Integrates vulnerability data and supply chain analysis
- **Dual authentication:** JWT (cookie-based) and API Key (header-based) authentication

### Supported Ecosystems
- Python (requirements.txt, pyproject.toml, setup.py, setup.cfg)
- JavaScript/Node.js (package.json, package-lock.json)
- Ruby (Gemfile, Gemfile.lock)
- Rust (Cargo.toml, Cargo.lock)
- Java (pom.xml)
- PHP (composer.json)

## 🏗️ Project Structure

```
securechain-depex/
├── app/
│   ├── controllers/          # API endpoints
│   │   ├── graph_controller.py           # Dependency graph management
│   │   ├── health_controller.py          # Health checks
│   │   ├── smt_operation_controller.py   # SMT operations (constraints)
│   │   └── ssc_operation_controller.py   # SSC operations (supply chain)
│   ├── services/             # Business logic
│   │   ├── package_service.py
│   │   ├── repository_service.py
│   │   ├── requirement_file_service.py
│   │   ├── version_service.py
│   │   ├── smt_service.py
│   │   └── operation_service.py
│   ├── domain/               # Domain logic
│   │   ├── repo_analyzer/    # Dependency file analyzers
│   │   │   └── requirement_files/  # Ecosystem-specific analyzers
│   │   ├── smt/              # SMT model and operations
│   │   │   ├── model/
│   │   │   ├── operations/
│   │   │   └── config_sanitizer/
│   │   └── repository_initializer.py
│   ├── schemas/              # Pydantic models
│   │   ├── enums/
│   │   ├── graphs/
│   │   ├── operations/
│   │   ├── messages/
│   │   └── validators/
│   ├── models/               # Database models (MongoDB documents)
│   │   └── api_key.py        # API Key model for authentication
│   ├── utils/                # Utilities
│   │   ├── api_key_bearer.py      # API Key authentication
│   │   ├── dual_auth_bearer.py    # Dual JWT + API Key auth
│   │   ├── jwt_bearer.py          # JWT authentication
│   │   └── ...
│   ├── exceptions/           # Custom exceptions
│   ├── apis/                 # External API clients (GitHub)
│   ├── database.py           # MongoDB configuration
│   ├── settings.py           # Application settings
│   └── main.py              # FastAPI entry point
├── tests/
│   ├── integration/          # Integration tests
│   └── unit/                # Unit tests
│       ├── controllers/
│       ├── services/
│       ├── domain/
│       ├── schemas/
│       └── utils/
├── dev/
│   ├── docker-compose.yml   # Development application container
│   └── Dockerfile           # Development Docker image (with --reload)
├── Dockerfile               # Production Docker image (optimized)
├── pyproject.toml           # Project configuration and dependencies
├── uv.lock                  # Locked dependencies for reproducibility
├── template.env             # Environment variables template
├── README.md                # User documentation
├── AUTHENTICATION.md        # Authentication documentation
└── CLAUDE.md               # This file - AI agent guide

Note: Database docker-compose.yml is in the Zenodo data dumps, not in this repo.
```

## 🧪 Testing

### Current Coverage Status (October 2025)
- **Total Coverage:** 84%
- **Total Tests:** 407 passing, 3 skipped
- **Tool:** pytest with pytest-cov

### Coverage by Module (Main Modules)
- `graph_controller.py`: 89% (10 tests)
- `ssc_operation_controller.py`: 94% (9 tests)
- `smt_operation_controller.py`: 51% (7 tests)
- `health_controller.py`: 100% (4 tests)
- `smt_model.py`: 100%
- `base_analyzer.py`: 95%
- `repository_service.py`: 100%
- `package_service.py`: 96%
- `api_key_bearer.py`: 92% (8 tests)
- `dual_auth_bearer.py`: 100% (9 tests)
- `jwt_bearer.py`: 52% (9 tests)

### Testing Conventions

#### 1. Async Tests
All controllers and services are asynchronous. Use `@pytest.mark.asyncio`:

```python
@pytest.mark.asyncio
async def test_endpoint(mock_service):
    response = await controller_function(...)
    assert response.status_code == 200
```

#### 2. Mocking Services
Services are injected via FastAPI Depends. In tests, use `AsyncMock`:

```python
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.fixture
def mock_service():
    mock = AsyncMock()
    mock.some_method.return_value = expected_value
    return mock
```

#### 3. Rate Limiting
Controllers use `@limiter.limit`. Patch the limiter in tests:

```python
@patch("app.controllers.controller_name.limiter")
async def test_endpoint(mock_limiter, ...):
    # Rate limiter is disabled in tests
```

#### 4. JSON Responses
FastAPI responses return `response.body` as bytes. Parse with `json.loads()`:

```python
import json

response = await endpoint(...)
response_data = json.loads(response.body)
assert response_data["key"] == "value"
```

#### 5. Enums
Use lowercase values with underscores for enums:

```python
from app.schemas.enums.node_type import NodeType

# ✅ Correct
node_type = NodeType.pypi_package
node_type = NodeType.cargo_package

# ❌ Incorrect
node_type = NodeType.PYPI_PACKAGE
```

#### 6. Controller Test Pattern
Common structure for endpoint tests:

```python
class TestController:
    @pytest.mark.asyncio
    @patch("app.controllers.controller_name.limiter")
    async def test_endpoint_success(
        self, mock_limiter, mock_request,
        mock_service1, mock_service2, mock_json_encoder
    ):
        # Arrange: Setup mocks
        mock_service1.method.return_value = expected_data
        
        request_obj = MagicMock()
        request_obj.field = "value"
        
        # Act: Call endpoint
        response = await endpoint_function(
            mock_request,
            request_obj,
            mock_service1,
            mock_service2,
            mock_json_encoder
        )
        
        # Assert: Validate response
        assert response.status_code == status.HTTP_200_OK
        response_data = json.loads(response.body)
        assert response_data["expected_field"] == expected_value
        
        # Verify: Check service calls
        mock_service1.method.assert_called_once_with(...)
    
    # Test endpoint with payload injection (for user-scoped operations)
    @pytest.mark.asyncio
    @patch("app.controllers.graph_controller.limiter")
    async def test_endpoint_with_user_context(
        self, mock_limiter, mock_request,
        mock_service, mock_json_encoder
    ):
        # Arrange: Mock the authenticated payload
        mock_payload = {"user_id": "user123"}
        
        mock_service.user_method.return_value = user_data
        
        # Act: Pass payload as parameter
        response = await endpoint_function(
            mock_request,
            mock_payload,  # ← Payload parameter
            mock_service,
            mock_json_encoder
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        # Verify service called with user_id from payload
        mock_service.user_method.assert_called_once_with("user123")
```

#### 7. Common Fixtures
Location: `tests/conftest.py`

```python
# Request mock
@pytest.fixture
def mock_request():
    request = MagicMock()
    request.state.limiter_checked = False
    return request

# JSON Encoder mock
@pytest.fixture
def mock_json_encoder():
    encoder = MagicMock()
    encoder.encode.side_effect = lambda x: x
    return encoder
```

#### 8. Testing Authentication Components
When testing authentication (ApiKeyBearer, DualAuthBearer):

```python
# ApiKeyBearer tests - Mock MongoDB
@pytest.mark.asyncio
async def test_api_key_bearer(api_key_bearer, mock_request):
    mock_request.headers = {"X-API-Key": "sk_test_key"}
    
    mock_collection = AsyncMock()
    mock_collection.find_one.return_value = {
        "key_hash": api_key_bearer.hash("sk_test_key"),
        "user_id": "user123",
        "is_active": True,
        "expires_at": None
    }
    
    with patch("app.utils.api_key_bearer.DatabaseManager") as mock_db:
        mock_db_instance = MagicMock()
        mock_db_instance.get_api_key_collection.return_value = mock_collection
        mock_db.return_value = mock_db_instance
        
        result = await api_key_bearer(mock_request)
        assert result["user_id"] == "user123"

# DualAuthBearer tests - Mock both bearer classes
@pytest.mark.asyncio
async def test_dual_auth(dual_auth_bearer, mock_request):
    mock_request.headers = {"X-API-Key": "sk_test"}
    
    with patch.object(ApiKeyBearer, "__call__", new_callable=AsyncMock, 
                      return_value={"user_id": "api_user"}):
        result = await dual_auth_bearer(mock_request)
        assert result["user_id"] == "api_user"
```

**Important:** 
- Mock `DatabaseManager` at class level for ApiKeyBearer tests
- Patch `ApiKeyBearer.__call__` and `JWTBearer.__call__` as class methods for DualAuthBearer tests
- Use `AsyncMock` for async authentication methods

### Testing Commands

```bash
# Run all tests
pytest
# Or with uv
uv run pytest

# Run tests with coverage
pytest --cov=app --cov-report=term-missing
# Or with uv
uv run pytest --cov=app --cov-report=term-missing

# Run tests from a specific module
pytest tests/unit/controllers/test_graph_controller.py -v

# Run with coverage for a specific module
pytest tests/unit/controllers/ -v --cov=app.controllers --cov-report=term-missing

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v

# Generate HTML coverage report
pytest --cov=app --cov-report=html
# Coverage report will be in htmlcov/index.html

# Run with specific markers
pytest -m unit          # Only unit tests
pytest -m integration   # Only integration tests
pytest -m "not slow"    # Skip slow tests
```

### Pytest Configuration
The project has comprehensive pytest configuration in `pyproject.toml`:
- **Markers:** `unit`, `integration`, `slow`, `database`
- **Auto coverage:** Automatically generates term, HTML, and XML reports
- **Async mode:** Automatically detects and runs async tests

## 🔑 Key Concepts

### 0. Authentication System
The API implements **dual authentication** supporting both JWT and API Key methods:

#### Authentication Flow
1. **DualAuthBearer** checks for API Key first (`X-API-Key` header)
2. If API Key present → validates with **ApiKeyBearer**
3. If no API Key → falls back to **JWTBearer** (cookie-based)
4. Both return `{"user_id": "..."}` on success

#### API Key Validation (`ApiKeyBearer`)
- **Format check:** Must start with `sk_` prefix
- **MongoDB lookup:** Queries `api_key` collection by hashed key (SHA-256)
- **Active status:** `is_active` must be `True`
- **Expiration check:** `expires_at` must be `None` or future datetime
- **Pydantic validation:** Uses `ApiKey` model for data validation
- **Returns:** `{"user_id": stored_key.user_id}`

#### API Key Model (`app/models/api_key.py`)
```python
class ApiKey(BaseModel):
    key_hash: str                          # SHA-256 hash of the API key
    user_id: str                           # User identifier
    name: Optional[str] = None             # Descriptive name
    created_at: datetime                   # Creation timestamp
    expires_at: Optional[datetime] = None  # Expiration (None = never expires)
    is_active: bool = True                 # Active status flag
```

#### Protected Endpoints (13 total)
- **Graph Controller (3):** `get_repositories`, `init_package`, `init_repository`
  - `get_repositories`: Uses payload to get `user_id` (no URL parameter needed)
  - `init_repository`: Uses payload to get `user_id` (removed from request body)
- **SMT Controller (7):** `valid_graph`, `minimize_impact`, `maximize_impact`, `filter_configs`, `valid_config`, `complete_config`, `config_by_impact`
- **SSC Controller (3):** `requirement_file_info`, `package_ssc_info`, `version_ssc_info`

#### Testing Authentication
```python
# Test ApiKeyBearer
@pytest.fixture
def api_key_bearer():
    return ApiKeyBearer()

@pytest.mark.asyncio
async def test_valid_api_key(api_key_bearer, mock_request):
    mock_request.headers = {"X-API-Key": "sk_valid_key_123"}
    
    # Mock MongoDB collection
    mock_collection = AsyncMock()
    mock_collection.find_one.return_value = {
        "key_hash": api_key_bearer.hash("sk_valid_key_123"),
        "user_id": "user123",
        "is_active": True,
        "expires_at": datetime.now(UTC) + timedelta(days=30)
    }
    
    with patch("app.utils.api_key_bearer.DatabaseManager") as mock_db:
        mock_db_instance = MagicMock()
        mock_db_instance.get_api_key_collection.return_value = mock_collection
        mock_db.return_value = mock_db_instance
        
        result = await api_key_bearer(mock_request)
        assert result["user_id"] == "user123"

# Test endpoint with payload injection
@pytest.mark.asyncio
@patch("app.controllers.graph_controller.limiter")
async def test_endpoint_with_payload(
    mock_limiter, mock_request, mock_service, mock_json_encoder
):
    # Simulate JWT/API Key payload
    mock_payload = {"user_id": "user123"}
    
    mock_service.some_method.return_value = expected_data
    
    response = await endpoint_function(
        mock_request,
        mock_payload,  # ← Payload parameter
        mock_service,
        mock_json_encoder
    )
    
    assert response.status_code == status.HTTP_200_OK
    # Verify service was called with user_id from payload
    mock_service.some_method.assert_called_once_with("user123")
```

For complete documentation, see [AUTHENTICATION.md](../AUTHENTICATION.md).

### 1. Dependency Graphs
The project builds graphs where:
- **Nodes:** Packages and specific versions
- **Edges:** Dependency relationships between packages
- **NodeType:** Enum that defines the package type (pypi_package, npm_package, cargo_package, etc.)

### 2. SMT Operations
The SMT (Satisfiability Modulo Theories) module resolves version constraints:
- `valid_graph`: Validates if a dependency graph is consistent
- `minimize_impact`: Finds configuration with minimum number of changes
- `maximize_impact`: Finds configuration with maximum number of updates
- `filter_configs`: Filters valid configurations
- `valid_config`: Validates a specific configuration
- `complete_config`: Completes a partial configuration
- `config_by_impact`: Orders configurations by impact

### 3. SSC Operations (Software Supply Chain)
Analyzes the software supply chain:
- `requirement_file_info`: Requirement file information
- `package_ssc_info`: SSC info for a package
- `version_ssc_info`: SSC info for a specific version

### 4. Operation Cache
The system caches operation results to improve performance:
- Uses MongoDB to store operations
- Checks if results are "stale" (outdated)
- Recomputes only when necessary

### 5. "no_dependencies" Response
Common pattern: when a graph has no dependencies (name is None), endpoints return:
```json
{
  "detail": "no_dependencies"
}
```
This is the simplest scenario and useful for quick coverage tests.

## 🔧 Main Dependencies

This project uses **uv** as the Python package manager, which is a fast Rust-based package and project manager for Python.

### Core Dependencies
```toml
[project]
name = "securechain-depex"
version = "1.1.0"
requires-python = ">=3.13"
dependencies = [
    "fastapi==0.116.1",           # Web framework
    "uvicorn==0.35.0",            # ASGI server
    "pydantic-settings==2.10.1",  # Settings management
    "motor==3.7.1",               # Async MongoDB driver
    "neo4j==5.28.1",              # Graph database driver
    "redis==5.2.1",               # Caching layer
    "z3-solver==4.15.3.0",        # SMT solver for constraints
    "apscheduler==3.11.0",        # Task scheduling
    "univers==31.0.0",            # Version parsing
    "slowapi==0.1.9",             # Rate limiting
    "pyjwt==2.10.1",              # JWT authentication
    "aiohttp==3.12.14",           # Async HTTP client
    "aiocache==0.12.3",           # Async caching
]
```

### Development Dependencies
```toml
[project.optional-dependencies]
dev = ["ruff==0.14.0"]           # Linting and formatting
test = [
    "pytest==8.4.2",
    "pytest-asyncio==1.2.0",
    "pytest-cov>=7.0.0",
    "httpx==0.28.1",              # Test client
]
```

### External Services
- **MongoDB:** Document database for storing operations, packages, versions, and **API keys**
  - Collections: `operations`, `packages`, `versions`, `repositories`, **`api_key`**
- **Neo4j:** Graph database for dependency graph storage and visualization
- **Redis:** In-memory cache for operation results
- **GitHub API:** Source code analysis and repository metadata

## 🐛 Known Issues and Solutions

### 1. init_package tests in graph_controller
**Problem:** Complex validation of `PackageMessageSchema` with `vendor` field.  
**Solution:** These tests were omitted. Current 89% coverage is acceptable.

### 2. Missing version_service parameter
**Problem:** Endpoints `valid_config` and `complete_config` require `version_service`.  
**Solution:** Ensure the `mock_version_service` fixture is passed as a parameter.

### 3. Rate Limiter in Tests
**Problem:** The `@limiter.limit` decorator expects a real Request object.  
**Solution:** Use `@patch("app.controllers.module_name.limiter")` to mock it.

### 4. Response Body is Bytes
**Problem:** `response.body` returns bytes, not dict.  
**Solution:** Use `json.loads(response.body)` to parse.

## 📝 Code Patterns

### Dependency Analyzers
All analyzers inherit from `BaseAnalyzer`:

```python
class CustomAnalyzer(BaseAnalyzer):
    def can_parse_file(self, filename: str) -> bool:
        return filename == "custom.lock"
    
    def extract_information(self, content: str) -> dict:
        # Parse content and return dependency info
        pass
```

### Controllers
Common pattern in controllers:

```python
# Pattern 1: Using payload to extract user_id (recommended for user-scoped operations)
@router.post("/endpoint")
@limiter.limit("10/minute")
async def endpoint_with_user_context(
    request: Request,
    request_data: RequestSchema,
    payload: dict = Depends(get_dual_auth_bearer()),  # ← Inject payload
    service1: Service1 = Depends(get_service1),
    service2: Service2 = Depends(get_service2),
    json_encoder: Encoder = Depends(get_encoder)
) -> Response:
    # Extract user_id from authenticated payload
    user_id = payload.get("user_id")
    
    # Use user_id in operations
    result = await service1.user_specific_operation(user_id, ...)
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder.encode(result)
    )

# Pattern 2: Using dependencies decorator (when user context not needed in logic)
@router.post("/endpoint")
@limiter.limit("10/minute")
async def endpoint_auth_only(
    request: Request,
    request_data: RequestSchema,
    service1: Service1 = Depends(get_service1),
    service2: Service2 = Depends(get_service2),
    json_encoder: Encoder = Depends(get_encoder)
) -> Response:
    # Authentication validated but user_id not used
    
    # 1. Read graph data
    graph_data = await service1.read_data(...)
    
    # 2. Validate if there are dependencies
    if graph_data["name"] is None:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"detail": "no_dependencies"}
        )
    
    # 3. Execute operation
    result = await service2.operation(...)
    
    # 4. Return result
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder.encode(result)
    )
```

**When to use each pattern:**
- **Pattern 1 (payload injection):** Use when you need the `user_id` for business logic (e.g., `get_repositories`, `init_repository`)
- **Pattern 2 (dependencies decorator):** Use when you only need to verify authentication without using user data (e.g., SMT operations, package status)

## 🎯 Areas with Low Coverage (Improvement Opportunities)

These modules have low test coverage and are priority areas for improvement:

1. **repository_initializer.py**: 23% → Target: 70%+
   - Repository initialization logic
   - Complex workflows with multiple services
   - Add tests for init flows and error handling

2. **repo_analyzer.py**: 24% → Target: 70%+
   - Main repository analysis orchestration
   - File discovery and analyzer selection
   - Test different repository structures

3. **database.py**: 31% → Target: 60%+
   - MongoDB connection and operations
   - Connection pooling and error handling
   - Mock database operations in tests

4. **github_service.py**: 32% → Target: 60%+
   - GitHub API integration
   - Repository metadata fetching
   - Mock GitHub API responses

5. **middleware.py**: 33% → Target: 80%+
   - Authentication middleware
   - CORS configuration
   - Request/response processing

### Coverage Improvement Strategy
1. Start with "happy path" scenarios
2. Add error handling tests
3. Test edge cases and boundary conditions
4. Mock external dependencies (GitHub API, databases)
5. Use fixtures to reduce test boilerplate

## 🚀 Development Commands

```bash
# Activate virtual environment (uv automatically creates and manages venvs)
source .venv/bin/activate

# Install dependencies with uv
uv sync

# Add a new dependency
uv add <package-name>

# Add a development dependency
uv add --dev <package-name>

# Run development server
uv run uvicorn app.main:app --reload

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=app --cov-report=term-missing

# Docker
docker-compose up -d

# Linting
uv run ruff check app/

# Formatting
uv run ruff format app/
```

### Docker Setup

The project uses Docker Compose for container orchestration.

**Docker Images:**
The project has TWO Dockerfiles for different purposes:
- **`Dockerfile`** (root): Production image with multi-stage build, optimized for size and performance
- **`dev/Dockerfile`**: Development image with hot-reload enabled (`--reload` flag)

**Important:** There are TWO separate docker-compose files in different locations:
- **Data dumps from Zenodo** contain a `docker-compose.yml` for database services (MongoDB, Neo4j, Redis)
- **`dev/docker-compose.yml`** in this repository is for the application container only

**Prerequisites:**
- Docker and Docker Compose installed
- Download [data dumps from Zenodo](https://doi.org/10.5281/zenodo.16739081) for database seeding
- Unzip the dumps folder (it contains its own docker-compose.yml)

**Setup Steps:**

1. **Create Docker network:**
   ```bash
   docker network create securechain
   ```

2. **Start databases (MongoDB, Neo4j, Redis):**
   Navigate to the unzipped data dumps folder and run:
   ```bash
   cd /path/to/unzipped/data-dumps
   docker compose up --build
   ```
   This will automatically seed the databases with the vulnerability and graph data.

3. **Start the application:**
   Return to the project root and run:
   ```bash
   cd /path/to/securechain-depex
   docker compose -f dev/docker-compose.yml up --build
   ```

4. **Access points:**
   - **Main API:** http://localhost:8002
   - **API Documentation:** http://localhost:8002/docs
   - **Auth API Documentation:** http://localhost:8001/docs
   - **Neo4j Browser:** http://localhost:7474/browser/
   - **MongoDB:** localhost:27017 (use MongoDB Compass)
   - **Redis:** localhost:6379

5. **Stop services:**
   ```bash
   # Stop databases (from data dumps folder)
   cd /path/to/unzipped/data-dumps
   docker compose down
   
   # Stop application (from project root)
   cd /path/to/securechain-depex
   docker compose -f dev/docker-compose.yml down
   ```

### Environment Configuration

The project requires environment variables for configuration. Follow these steps:

1. **Copy template:**
   ```bash
   cp template.env app/.env
   ```

2. **Required variables in `app/.env`:**

   ```bash
   # GitHub API (required for repository analysis)
   GITHUB_TOKEN=your_github_token_here
   
   # JWT Configuration (required for authentication)
   JWT_SECRET=your_secret_key_here
   JWT_ALGORITHM=HS256
   
   # MongoDB
   MONGODB_URL=mongodb://localhost:27017
   MONGODB_DATABASE=depex
   
   # Neo4j
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password
   
   # Redis
   REDIS_HOST=localhost
   REDIS_PORT=6379
   ```

3. **Get GitHub token:**
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Generate new token (classic)
   - Required scopes: `repo`, `read:org`
   - [Documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

4. **Generate JWT secret:**
   ```bash
   openssl rand -base64 32
   ```
   Copy the output and use it as `JWT_SECRET`

### Why uv?
- **Fast:** Written in Rust, significantly faster than pip/poetry
- **Deterministic:** Lock file ensures reproducible installations
- **Modern:** Built-in virtual environment management
- **Compatible:** Works with standard Python packaging (pyproject.toml)

### Docker Images Explained

The project provides two Dockerfiles optimized for different use cases:

#### Production (`Dockerfile` in root)
- **Multi-stage build:** Separates build and runtime stages for smaller image
- **Optimized:** Only production dependencies, no dev tools
- **Size optimized:** Smaller final image size
- **No hot-reload:** Requires rebuild for code changes
- **Use case:** Production deployments, CI/CD pipelines

**Key features:**
```dockerfile
FROM python:3.13-slim AS builder  # Build stage
RUN uv sync --frozen --no-cache   # Install all dependencies

FROM python:3.13-slim AS runtime  # Runtime stage (smaller)
COPY --from=builder /build/.venv  # Only copy installed packages
CMD ["uvicorn", "app.main:app"]   # No reload flag
```

#### Development (`dev/Dockerfile`)
- **Single-stage:** Simpler build process
- **Hot-reload enabled:** `--reload` flag for automatic code updates
- **Dev dependencies excluded:** Uses `--no-dev` flag
- **Fast iteration:** Code changes reflect immediately
- **Use case:** Local development, debugging

**Key features:**
```dockerfile
FROM python:3.13-slim              # Single stage
RUN uv sync --frozen --no-dev      # No dev dependencies (tests, linters)
CMD ["uvicorn", "app.main:app", "--reload"]  # Hot-reload enabled
```

**When to use which:**
- **Development:** Use `dev/Dockerfile` with `dev/docker-compose.yml`
- **Production:** Use root `Dockerfile` (manual build or production docker-compose)
- **Testing:** Use development setup with mounted volumes for code changes

## 📚 Useful References

- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Pytest Docs:** https://docs.pytest.org/
- **Z3 Solver:** https://github.com/Z3Prover/z3
- **Pydantic V2:** https://docs.pydantic.dev/latest/
- **uv:** https://docs.astral.sh/uv/
- **Neo4j Python Driver:** https://neo4j.com/docs/python-manual/current/
- **Motor (Async MongoDB):** https://motor.readthedocs.io/
- **Univers (Version Parsing):** https://github.com/aboutcode-org/univers
- **Secure Chain Docs:** https://securechaindev.github.io/
- **Project Repository:** https://github.com/securechaindev/securechain-depex
- **Data Dumps:** https://doi.org/10.5281/zenodo.16739081 (Required for full deployment)

## 🏛️ Architecture & Design Decisions

### Database Strategy
1. **MongoDB:** Primary data store for operations, packages, versions, and repositories
   - Flexible schema for different package ecosystems
   - Fast document-based queries
   - Operation caching with TTL

2. **Neo4j:** Graph database for dependency relationships
   - Visualize dependency trees
   - Complex graph queries (transitive dependencies)
   - Path finding and impact analysis

3. **Redis:** In-memory cache
   - Fast operation result caching
   - Rate limiting state
   - Temporary data storage

### Authentication & Security
- **Dual authentication system:** 
  - **JWT (Primary):** Cookie-based authentication with `auth_token` cookie
  - **API Key (Alternative):** Header-based authentication with `X-API-Key` header
  - **Priority:** API Key takes precedence over JWT when both are provided
- **API Key validation:** MongoDB-backed with SHA-256 hashing, active status, and expiration checks
- **Rate limiting:** SlowAPI implementation to prevent abuse (10/minute per endpoint)
- **CORS middleware:** Configured for cross-origin requests
- **Environment-based secrets:** All sensitive data in `.env` files
- **Protected endpoints:** 13 endpoints across graph, SMT, and SSC controllers use dual authentication

### Async Architecture
- **Fully asynchronous:** All I/O operations are async (DB, HTTP, file operations)
- **Motor:** Async MongoDB driver
- **aiohttp:** Async HTTP client for GitHub API
- **FastAPI:** Native async support for high concurrency

### Code Quality Tools
- **Ruff:** Fast Python linter and formatter (replaces flake8, black, isort)
- **Pytest:** Test framework with async support
- **Coverage:** pytest-cov for code coverage tracking
- **Type hints:** Extensive use of Python type annotations with Pydantic

## 💡 Tips for AI Agents

1. **Before modifying tests:** Always verify the current state with `read_file`
2. **To improve coverage:** Focus first on "no_dependencies" scenarios (quick and effective)
3. **When creating controller tests:** Always include fixtures for services, request and json_encoder
4. **JSON responses:** Remember to use `json.loads(response.body)` in assertions
5. **Async/Await:** All endpoints and services are asynchronous
6. **Mocking:** Use `AsyncMock` for services, `MagicMock` for simple objects
7. **Rate Limiting:** Always patch the limiter with `@patch`
8. **Run tests after changes:** Validate that everything works with `uv run pytest`
9. **Package management:** Use `uv add` to add dependencies, `uv sync` to install/update
10. **Database operations:** Always use Motor (async) for MongoDB, not pymongo
11. **Version parsing:** Use `univers` library for version comparison and parsing
12. **Graph operations:** Neo4j queries should use the official driver with async support
13. **Configuration:** Settings are managed through Pydantic Settings, loaded from `.env`
14. **Ruff formatting:** Use `uv run ruff format` instead of black

## 🔍 Common Development Workflows

### Adding a New Dependency Analyzer

1. Create new analyzer in `app/domain/repo_analyzer/requirement_files/`
2. Inherit from `BaseAnalyzer`
3. Implement `can_parse_file()` and `extract_information()`
4. Register in `analyzer_registry.py`
5. Add tests in `tests/unit/domain/analyzers/`

### Adding a New SMT Operation

1. Create operation file in `app/domain/smt/operations/`
2. Implement operation logic using Z3 solver
3. Add endpoint in `smt_operation_controller.py`
4. Create request schema in `app/schemas/operations/`
5. Add tests in `tests/unit/controllers/`

### Adding a New Controller Endpoint

1. Define request/response schemas in `app/schemas/`
2. Implement business logic in appropriate service
3. Add endpoint in controller with rate limiting
4. Add dependency injection for services
5. Create comprehensive tests with mocks
6. Update this documentation if needed

## 📊 Project Metrics & Goals

### Current State (October 2025)
- **Version:** 1.1.0
- **Test Coverage:** 84% (407 tests)
- **Python Version:** 3.13+
- **License:** GPL-3.0-or-later
- **Active Development:** Yes

### Coverage Goals
- **Target:** 90% overall coverage
- **Priority Areas:**
  - repository_initializer.py (23% → 70%+)
  - repo_analyzer.py (24% → 70%+)
  - database.py (31% → 60%+)
  - github_service.py (32% → 60%+)

### Performance Considerations
- Rate limiting: 10 requests/minute per endpoint
- Cache TTL: Configurable per operation type
- Async I/O: All database and HTTP operations
- Connection pooling: MongoDB and Neo4j drivers

## 🤝 Contributing Guidelines

When contributing to this project:

1. **Follow existing patterns:** Controllers, services, domain separation
2. **Write tests first:** TDD approach preferred
3. **Use type hints:** All functions should have proper type annotations
4. **Document complex logic:** Add docstrings for non-trivial functions
5. **Keep async:** Never use blocking I/O operations
6. **Update this guide:** Add new patterns or important details
7. **Run linter:** `uv run ruff check app/` before committing
8. **Check coverage:** Maintain or improve coverage percentage
9. **Test locally:** Run full test suite before pushing
10. **Follow commit conventions:** Clear, descriptive commit messages

### Pull Request Process

1. **Fork and clone** the repository
2. **Create a feature branch:** `git checkout -b feature/your-feature-name`
3. **Make your changes** with tests
4. **Run tests:** `uv run pytest --cov=app`
5. **Run linter:** `uv run ruff check app/`
6. **Format code:** `uv run ruff format app/`
7. **Commit changes:** Clear commit message describing the change
8. **Push to your fork:** `git push origin feature/your-feature-name`
9. **Open a Pull Request** with description of changes
10. **Wait for review** and address feedback

### Code Review Checklist

- [ ] All tests pass
- [ ] Coverage is maintained or improved
- [ ] No linting errors
- [ ] Code is properly formatted
- [ ] Type hints are used
- [ ] Docstrings for complex functions
- [ ] No blocking I/O operations
- [ ] Environment variables documented if added
- [ ] README or CLAUDE.md updated if needed

For major changes, please **open an issue first** to discuss what you would like to change.

## � Troubleshooting

### Common Issues and Solutions

#### Tests Failing

**Problem:** Tests fail with `AttributeError: 'Depends' object has no attribute 'encode'`  
**Solution:** Missing service parameter in function call. Ensure all required dependencies are passed as parameters.

**Problem:** Tests fail with rate limiter errors  
**Solution:** Add `@patch("app.controllers.module_name.limiter")` decorator to test function.

**Problem:** Async tests not running  
**Solution:** Add `@pytest.mark.asyncio` decorator to async test functions.

#### Import Errors

**Problem:** `ModuleNotFoundError` when running tests  
**Solution:** Ensure you're in the virtual environment and dependencies are installed: `uv sync`

**Problem:** Imports work in IDE but fail in tests  
**Solution:** Run tests from project root, not from test directory.

#### Database Connection Issues

**Problem:** MongoDB connection timeout  
**Solution:** Ensure MongoDB container is running: `docker ps | grep mongo`

**Problem:** Neo4j authentication failed  
**Solution:** Check Neo4j credentials in `.env` file match container settings.

**Problem:** Redis connection refused  
**Solution:** Verify Redis container is running on port 6379.

#### Docker Issues

**Problem:** `docker network create securechain` fails  
**Solution:** Network might already exist. Check with `docker network ls`

**Problem:** Port already in use (8002, 27017, 7687, 6379)  
**Solution:** Stop conflicting services or change ports in docker-compose.yml files

**Problem:** Database not seeded  
**Solution:** Ensure data dumps are downloaded and unzipped. Run `docker compose up` from inside the data dumps folder, NOT from the project root.

**Problem:** Can't find docker-compose.yml in project root  
**Solution:** The database docker-compose.yml is inside the Zenodo data dumps, not in the project repository. Only `dev/docker-compose.yml` is in the repo.

#### Coverage Issues

**Problem:** Coverage report shows lower than expected  
**Solution:** Run tests with `--cov=app` flag to ensure all app code is measured.

**Problem:** HTML coverage report not generated  
**Solution:** Add `--cov-report=html` flag or check `htmlcov/` directory.

#### Development Issues

**Problem:** uv command not found  
**Solution:** Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`

**Problem:** Changes not reflected when running app  
**Solution:** Use `--reload` flag: `uv run uvicorn app.main:app --reload`

**Problem:** Ruff format changes files unexpectedly  
**Solution:** Ruff follows configured rules in `pyproject.toml`. Review changes before committing.

### Getting Help

If you encounter issues not listed here:
1. Check the [GitHub Issues](https://github.com/securechaindev/securechain-depex/issues)
2. Review the [official documentation](https://securechaindev.github.io/)
3. Contact the team at hi@securechain.dev

## 📅 Last Update

**Date:** November 8, 2025  
**Version:** 1.1.0  
**Coverage:** 84%  
**Tests:** 407 passing, 3 skipped  
**Latest Improvement:** Refactored graph controller endpoints to use payload injection for user context
- `get_repositories`: Changed from `/repositories/{user_id}` to `/repositories` (user_id from payload)
- `init_repository`: Removed `user_id` from request body, now extracted from payload
- Improved security by preventing user_id manipulation in requests
**Authentication Tests:** 17 tests (8 ApiKeyBearer + 9 DualAuthBearer)  
**Python Version:** 3.13+  
**Package Manager:** uv

---

*This document should be updated when significant changes are made to the architecture, testing patterns, or project structure.*

## 📧 Contact & Support

- **Team:** Secure Chain Team (hi@securechain.dev)
- **Organization:** https://github.com/securechaindev
- **Documentation:** https://securechaindev.github.io/
- **Issues:** https://github.com/securechaindev/securechain-depex/issues
