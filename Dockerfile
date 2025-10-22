FROM python:3.13-slim AS builder

WORKDIR /build

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml uv.lock README.md ./

RUN /root/.local/bin/uv sync --frozen --no-group dev --no-cache

FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/build/.venv/bin:$PATH"

WORKDIR /app

COPY --from=builder /build/.venv /build/.venv

COPY ./app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]