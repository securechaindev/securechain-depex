FROM python:3.14-slim AS builder

ENV UV_SYSTEM_PYTHON=1

WORKDIR /build

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock README.md ./

RUN uv sync --frozen --no-cache

FROM python:3.14-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/build/.venv/bin:$PATH"

WORKDIR /

COPY --from=builder /build/.venv /build/.venv

RUN apt-get update \
 && apt-get install -y --no-install-recommends git \
 && rm -rf /var/lib/apt/lists/*

COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]