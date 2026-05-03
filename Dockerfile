FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app/ ./app/

CMD ["uv", "run", "python", "-m", "app.main", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "--db-host", "db", \
     "--db-port", "3306", \
     "--db-user", "mywebapp", \
     "--db-password", "securepass123", \
     "--db-name", "mywebapp"]
