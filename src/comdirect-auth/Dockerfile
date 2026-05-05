FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    cmake \
    && rm -rf /var/lib/apt/lists/*

COPY plumbing_core /app/plumbing_core

# Change the working directory to the `app` directory
WORKDIR /app/comdirect-auth

# Install dependencies in a cache layer. This speeds up build time
RUN --mount=type=cache,target=/root/.cache/uv \
  --mount=type=bind,source=comdirect-auth/uv.lock,target=uv.lock \
  --mount=type=bind,source=comdirect-auth/pyproject.toml,target=pyproject.toml \
  uv sync --locked --no-install-project --no-editable

# Copy the project into the intermediate image
COPY comdirect-auth /app/comdirect-auth

# Sync the project and install it, now that we have access to the source code
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --locked --no-editable --no-dev

FROM python:3.12-slim

# Create a non-root user and group with specific IDs
RUN groupadd --gid 1000 app && useradd --uid 1000 --gid 1000 --no-create-home --shell /bin/sh app

# Copy the environment, but not the source code
COPY --from=builder --chown=app:app /app/comdirect-auth/.venv /app/comdirect-auth/.venv

# Switch to the non-root user
USER app

# Run the application using the compiled app command
CMD ["/app/comdirect-auth/.venv/bin/comdirect-auth"]
