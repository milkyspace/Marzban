# Build stage
ARG PYTHON_VERSION=3.12
FROM ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-bookworm-slim

# Set up the working directory
WORKDIR /code
COPY . /code

# Enable bytecode compilation and use copy mode instead of linking
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Install dependencies using uv
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Put the virtual environment binaries in the PATH
ENV PATH="/code/.venv/bin:$PATH"

# Create CLI wrapper
COPY cli_wrapper.sh /usr/bin/marzban-cli
RUN chmod +x /usr/bin/marzban-cli

# Set the entrypoint
# Adjust to use the venv path as needed
ENTRYPOINT ["bash", "-c", "/code/.venv/bin/python -m alembic upgrade head"]
CMD ["bash", "-c", "/code/.venv/bin/python main.py"]