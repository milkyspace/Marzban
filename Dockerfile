# Build stage
ARG PYTHON_VERSION=3.12
FROM python:$PYTHON_VERSION-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up the working directory
WORKDIR /build
COPY . /build

# Copy uv from its container
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install dependencies using uv
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Final stage
FROM python:$PYTHON_VERSION-slim

# Set up the working directory
RUN mkdir /code
WORKDIR /code

# Copy uv from the builder stage
COPY --from=builder /bin/uv /bin/uvx /bin/

# Copy the Python packages - adjust this path based on where uv installs packages
COPY --from=builder /root/.cache/uv/install /root/.cache/uv/install
COPY --from=builder /root/.local /root/.local

# Copy your application code
COPY . /code

# Copy and set up the CLI wrapper
COPY cli_wrapper.sh /usr/bin/marzban-cli
RUN chmod +x /usr/bin/marzban-cli

# Set the entrypoint
ENTRYPOINT ["bash", "-c", "uv run alembic upgrade head"]
CMD ["bash", "-c", "uv run main.py"]