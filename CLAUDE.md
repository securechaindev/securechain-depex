# AI Agent Guide - SecureChain DepEx

## 📏 Document Guidelines

**IMPORTANT:** This document must follow these strict rules:
1. **Maximum Length:** 500 lines - keep content concise and relevant
2. **Content Focus:** Only include essential project context, patterns, and frequently needed information
3. **Regular Cleanup:** Remove outdated or rarely used sections to stay under the limit

When updating this document, prioritize keeping the most critical and frequently referenced information.

## ⚡ Quick Start

**Project Type:** FastAPI async web application for software supply chain analysis

**Key Info:**
- Python 3.14+ with `uv` package manager
- Test Coverage: 84% (514 tests)
- Tech Stack: FastAPI, MongoDB, Neo4j, Redis, Z3 solver
- All I/O operations are async

**Common Commands:**
```bash
uv run pytest --cov=app              # Run tests with coverage
uv add package-name                  # Add dependency
uv run ruff format app/              # Format code
uv run ruff check app/               # Check linting
```

**Critical Patterns:**
- Controllers use `@limiter.limit` - always patch in tests
- Response bodies are bytes - use `json.loads(response.body)`
- Services use AsyncMock, simple objects use MagicMock
- Enum values: lowercase with underscores (`NodeType.pypi_package`)

## 📋 Project Overview

**SecureChain DepEx** analyzes software supply chain dependencies across multiple ecosystems (Python, JavaScript, Ruby, Rust, Java, PHP) and performs SMT operations to resolve version constraints.

**Supported Files:**
- Python: requirements.txt, pyproject.toml, setup.py, setup.cfg
- JavaScript: package.json, package-lock.json
- Ruby: Gemfile, Gemfile.lock
- Rust: Cargo.toml, Cargo.lock
- Java: pom.xml
- .NET: packages.config
- **SBOM:** CycloneDX and SPDX formats (JSON/XML)
  - Files: bom.json, sbom.json, *.cdx.json, bom.xml, sbom.xml, *.spdx.json, *.spdx.xml
  - Multi-ecosystem support (PyPI, NPM, Maven, Cargo, RubyGems, NuGet)

## 🏗️ Project Structure

```
app/
├── controllers/     # API endpoints (graph, health, smt, ssc)
├── services/        # Business logic (package, repository, version, smt, operation)
├── domain/          # Domain logic (analyzers, smt model, repository initializer)
├── schemas/         # Pydantic models (request/response validation)
├── models/          # Database models (MongoDB documents)
├── utils/           # Utilities (auth, json encoding, redis queue)
├── exceptions/      # Custom exceptions
└── apis/            # External API clients (GitHub)

tests/
├── integration/     # Integration tests
└── unit/            # Unit tests (controllers, services, domain, schemas, utils)
```

## 🧪 Testing

**Coverage:** 84% (407 tests)

**Key Conventions:**

1. **Async Tests:**
```python
@pytest.mark.asyncio
async def test_endpoint(mock_service):
    response = await controller_function(...)
    assert response.status_code == 200
```

2. **Mocking Services:**
```python
@pytest.fixture
def mock_service():
    mock = AsyncMock()
    mock.some_method.return_value = expected_value
    return mock
```

3. **Rate Limiting:**
```python
@patch("app.controllers.controller_name.limiter")
async def test_endpoint(mock_limiter, ...):
    # Rate limiter is disabled
```

4. **JSON Responses:**
```python
import json
response = await endpoint(...)
response_data = json.loads(response.body)
assert response_data["key"] == "value"
```

5. **Controller Test Pattern:**
```python
class TestController:
    @pytest.mark.asyncio
    @patch("app.controllers.controller_name.limiter")
    async def test_endpoint_success(
        self, mock_limiter, mock_request,
        mock_service, mock_json_encoder
    ):
        # Arrange
        mock_service.method.return_value = expected_data
        
        # Act
        response = await endpoint_function(
            mock_request, request_obj,
            mock_service, mock_json_encoder
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        response_data = json.loads(response.body)
        assert response_data["field"] == expected_value
        
        # Verify
        mock_service.method.assert_called_once_with(...)
```

6. **Endpoints with User Context:**
```python
@pytest.mark.asyncio
@patch("app.controllers.graph_controller.limiter")
async def test_endpoint_with_payload(
    mock_limiter, mock_request, mock_service, mock_json_encoder
):
    # Mock authenticated payload
    mock_payload = {"user_id": "user123"}
    
    mock_service.user_method.return_value = user_data
    
    # Pass payload as parameter
    response = await endpoint_function(
        mock_request, mock_payload,
        mock_service, mock_json_encoder
    )
    
    # Verify service called with user_id from payload
    mock_service.user_method.assert_called_once_with("user123")
```

**Common Fixtures (tests/conftest.py):**
```python
@pytest.fixture
def mock_request():
    request = MagicMock()
    request.state.limiter_checked = False
    return request

@pytest.fixture
def mock_json_encoder():
    encoder = MagicMock()
    encoder.encode.side_effect = lambda x: x
    return encoder
```

## 🔑 Authentication

**Dual Authentication System:** JWT (cookie) + API Key (header)

**Flow:**
1. DualAuthBearer checks for API Key first (`X-API-Key` header)
2. If API Key present → validates with ApiKeyBearer
3. If no API Key → falls back to JWTBearer (cookie-based)
4. Both return `{"user_id": "..."}` on success

**API Key Validation:**
- Format: Must start with `sk_` prefix
- Storage: MongoDB `api_key` collection (SHA-256 hashed)
- Validation: Active status + expiration check

**API Key Model:**
```python
class ApiKey(BaseModel):
    key_hash: str                          # SHA-256 hash
    user_id: str                           # User identifier
    name: Optional[str] = None             # Descriptive name
    created_at: datetime                   # Creation timestamp
    expires_at: Optional[datetime] = None  # Expiration (None = never)
    is_active: bool = True                 # Active status
```

**Protected Endpoints (15 total):**
- Graph Controller (5): `get_repositories`, `init_package`, `init_repository`, `expand_package`, `expand_version`
- SMT Controller (7): `valid_graph`, `minimize_impact`, `maximize_impact`, `filter_configs`, `valid_config`, `complete_config`, `config_by_impact`
- SSC Controller (3): `requirement_file_info`, `package_ssc_info`, `version_ssc_info`

**Testing Authentication:**
```python
# ApiKeyBearer test
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
```

## 📝 Code Patterns

### Controllers

**Pattern 1: With User Context (Payload Injection)**
```python
@router.post("/endpoint")
@limiter.limit("10/minute")
async def endpoint_with_user(
    request: Request,
    request_data: RequestSchema,
    payload: dict = Depends(get_dual_auth_bearer()),  # Inject payload
    service: Service = Depends(get_service),
    json_encoder: Encoder = Depends(get_encoder)
) -> Response:
    user_id = payload.get("user_id")
    result = await service.user_specific_operation(user_id, ...)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder.encode(result)
    )
```

**Pattern 2: Auth Only (No User Context)**
```python
@router.post("/endpoint", dependencies=[Depends(get_dual_auth_bearer())])
@limiter.limit("10/minute")
async def endpoint_auth_only(
    request: Request,
    request_data: RequestSchema,
    service: Service = Depends(get_service),
    json_encoder: Encoder = Depends(get_encoder)
) -> Response:
    # 1. Read graph data
    graph_data = await service.read_data(...)
    
    # 2. Validate dependencies
    if graph_data["name"] is None:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"detail": "no_dependencies"}
        )
    
    # 3. Execute operation
    result = await service.operation(...)
    
    # 4. Return result
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder.encode(result)
    )
```

### Neo4j Query Optimization

**Graph Expansion Endpoints:** `expand_package` and `expand_version` build response structure directly in Neo4j queries (not in Python).

**Example Pattern:**
```python
# Service (version_service.py or package_service.py)
async def read_expansion_data(self, purl: str) -> dict[str, Any] | None:
    query = """
    MATCH (parent)-[:RELATION]->(child)
    WITH parent, collect(child) AS children
    RETURN {
        nodes: [c IN children | {
            id: c.purl,
            label: c.name,
            type: labels(c)[0],
            props: {
                name: c.name,
                purl: c.purl,
                // ... other properties
            }
        }],
        edges: [c IN children | {
            id: 'e-' + $parent_purl + '-' + c.purl,
            source: $parent_purl,
            target: c.purl,
            type: 'RELATION_TYPE'
        }]
    } AS expansion_data
    """
    # Execute query and return directly

# Controller
async def expand_endpoint(
    request: Request,
    expand_request: ExpandRequest,
    service: Service = Depends(get_service),
    json_encoder: JSONEncoder = Depends(get_encoder)
) -> JSONResponse:
    expansion_data = await service.read_expansion_data(
        expand_request.purl
    )
    if expansion_data is None:
        return JSONResponse(status_code=404, ...)
    
    # Return data directly without processing
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder.encode({
            "code": "SUCCESS",
            "data": expansion_data  # Already formatted by Neo4j
        })
    )
```

**Benefits:**
- Reduces data transfer between Neo4j and Python
- Less CPU overhead (no list comprehensions in Python)
- Single source of truth for data structure
- Easier to maintain and test

### Dependency Analyzers

```python
class CustomAnalyzer(BaseAnalyzer):
    def can_parse_file(self, filename: str) -> bool:
        return filename == "custom.lock"
    
    def extract_information(self, content: str) -> dict:
        # Parse content and return dependency info
        pass
```

## 🔧 Dependencies

**Core:**
- fastapi==0.116.1
- uvicorn==0.35.0
- PyMongo==4.15.4 (async MongoDB)
- neo4j==5.28.1
- redis==5.2.1
- z3-solver==4.15.3.0
- pyjwt==2.10.1

**Dev:**
- ruff==0.14.0
- pytest==8.4.2
- pytest-asyncio==1.2.0
- pytest-cov>=7.0.0

## 🚀 Development

**Setup:**
```bash
# Install dependencies
uv sync

# Environment
cp template.env app/.env
# Edit app/.env with required values

# Run development server
uv run uvicorn app.main:app --reload

# Run tests
uv run pytest --cov=app
```

**Docker:**
```bash
# Create network
docker network create securechain

# Start databases (from data dumps folder)
cd /path/to/data-dumps
docker compose up --build

# Start application (from project root)
docker compose -f dev/docker-compose.yml up --build
```

**Access Points:**
- API: http://localhost:8002
- API Docs: http://localhost:8002/docs
- Neo4j: http://localhost:7474/browser/
- MongoDB: localhost:27017
- Redis: localhost:6379

## 🏛️ Architecture

**Database Strategy:**
1. **MongoDB:** Operations, packages, versions, repositories, API keys
2. **Neo4j:** Dependency graphs and relationships
3. **Redis:** Operation result caching, rate limiting

**Async Architecture:**
- All I/O operations are async (DB, HTTP, file operations)
- PyMongo async driver for MongoDB, aiohttp for HTTP, Neo4j async driver
- Neo4j query optimization: Build response structures in Cypher

**Security:**
- Dual authentication (JWT + API Key)
- Rate limiting (10/minute per endpoint)
- CORS middleware
- Environment-based secrets

## 🐛 Known Issues

1. **init_package tests:** Complex validation omitted (89% coverage acceptable)
2. **Rate limiter:** Always patch with `@patch("app.controllers.module.limiter")`
3. **Response body:** Use `json.loads(response.body)` to parse
4. **Version service:** Some endpoints require `mock_version_service` fixture

## 💡 Tips for AI Agents

1. Verify current state with `read_file` before modifying
2. Focus on "no_dependencies" scenarios first (quick coverage)
3. Always include service, request, and json_encoder fixtures
4. Use AsyncMock for services, MagicMock for simple objects
5. All operations are async - never use blocking I/O
6. Run tests after changes: `uv run pytest`
7. Use `uv add` to add dependencies
8. Neo4j queries should build response structures in Cypher for graph expansion endpoints

## 📊 Metrics

- Version: 1.1.3
- Coverage: 84% (514 tests)
- Python: 3.14+
- License: GPL-3.0-or-later

**Low Coverage Areas (Improvement Opportunities):**
- repository_initializer.py: 20% → 70%+
- repo_analyzer.py: 23% → 70%+
- database.py: 32% → 60%+
- github_service.py: 32% → 60%+

## 🔍 Troubleshooting

**Tests Failing:**
- Missing service parameter → Add to function call
- Rate limiter error → Add `@patch` decorator
- Async tests not running → Add `@pytest.mark.asyncio`

**Imports:**
- ModuleNotFoundError → Run `uv sync`
- Imports fail in tests → Run from project root

**Database:**
- MongoDB timeout → Check container: `docker ps | grep mongo`
- Neo4j auth failed → Verify `.env` credentials
- Redis refused → Verify container on port 6379

**Docker:**
- Port in use → Stop conflicting services
- Database not seeded → Download/unzip data dumps, run compose from dumps folder
- Can't find docker-compose → Database compose is in Zenodo dumps, not repo

## 📚 References

- FastAPI: https://fastapi.tiangolo.com/
- uv: https://docs.astral.sh/uv/
- Neo4j Python: https://neo4j.com/docs/python-manual/current/
- PyMongo: https://pymongo.readthedocs.io/en/stable/api/pymongo/asynchronous/index.html
- Secure Chain: https://securechaindev.github.io/
- Repository: https://github.com/securechaindev/securechain-depex
- Data Dumps: https://doi.org/10.5281/zenodo.16739081

## 📅 Last Update

**Date:** November 20, 2025
**Version:** 1.1.3
**Coverage:** 84% (514 tests)

---

*Keep this document under 500 lines. Remove outdated content regularly.*
