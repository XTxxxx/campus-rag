FROM python:3.10-slim-bookworm AS builder

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

ADD https://astral.sh/uv/0.6.17/install.sh /uv-installer.sh

RUN sh /uv-installer.sh && rm /uv-installer.sh

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app
COPY pyproject.toml .
COPY uv.lock .

RUN mkdir -p src

RUN uv sync --locked

COPY data ./data
COPY src ./src


FROM python:3.10-slim-bookworm

WORKDIR /app

COPY --from=builder /app /app
COPY --from=builder /root/.local /root/.local


ENV PATH="/root/.local/bin:$PATH"

CMD ["uv", "run", "fastapi", "run", "src/campus_rag/api/main.py", "--port", "8000", "--host", "0.0.0.0"]
