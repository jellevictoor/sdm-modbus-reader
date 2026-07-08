FROM python:3.12-slim

# uv for reproducible, lockfile-pinned installs
COPY --from=ghcr.io/astral-sh/uv:0.6.14 /uv /uvx /bin/

WORKDIR /app

# System dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Add user to dialout group for serial port access
RUN usermod -a -G dialout root

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install locked dependencies first (cached unless the lock changes)
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

# Install the project itself
COPY sdm_modbus_reader ./sdm_modbus_reader
RUN uv sync --frozen --no-dev

# Put the project venv on PATH so the console script resolves directly
ENV PATH="/app/.venv/bin:$PATH"

# Expose the web interface port
EXPOSE 8000

# Use sdm-reader as entrypoint
ENTRYPOINT ["sdm-reader"]

# Default arguments (can be overridden in docker-compose)
CMD []
