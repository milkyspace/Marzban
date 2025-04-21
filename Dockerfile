ARG PYTHON_VERSION=3.12
FROM python:$PYTHON_VERSION-slim

# Install build dependencies for psutil
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up the working directory
RUN mkdir /code
WORKDIR /code
COPY . /code
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install dependencies using uv
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Create CLI wrapper
COPY ./cli_wrapper /usr/bin/marzban-cli
RUN chmod +x /usr/bin/marzban-cli

# Set the entrypoint
ENTRYPOINT ["bash", "-c", "uv run alembic upgrade head"]
CMD ["bash", "-c", "uv run main.py"]