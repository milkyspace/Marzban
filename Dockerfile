ARG PYTHON_VERSION=3.12

# Build stage
FROM python:$PYTHON_VERSION-slim AS builder

# Install build dependencies for psutil
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Change the working directory to the `build` directory
WORKDIR /build

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-editable

# Copy the project into the intermediate image
COPY . /build

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-editable

# Final stage
FROM python:$PYTHON_VERSION-slim

# Create code directory
RUN mkdir -p /code
WORKDIR /code

# Copy the environment from builder
COPY --from=builder /build/.venv /code/.venv

# Copy your application code
COPY . /code

# Add virtual environment to PATH
ENV PATH="/code/.venv/bin:$PATH"

# Copy and setup CLI wrapper
COPY cli_wrapper.sh /usr/bin/marzban-cli
RUN chmod +x /usr/bin/marzban-cli

# Set the entrypoint
ENTRYPOINT ["bash", "-c", "/code/.venv/bin/python -m alembic upgrade head"]
CMD ["bash", "-c", "/code/.venv/bin/python /code/main.py"]