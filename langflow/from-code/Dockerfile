# syntax=docker/dockerfile:1
################################
# BUILDER STAGE
################################
# Use the uv pre-installed Python 3.12 image (bookworm-slim) as our builder.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# Set the working directory for building the project.
WORKDIR /app

# Enable bytecode compilation and set uv's linking mode.
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Update packages and install build tools, git, npm, and gcc.
RUN apt-get update && apt-get upgrade -y && \
    apt-get install --no-install-recommends -y \
        build-essential \
        git \
        npm \
        gcc && \
    apt-get clean && rm -rf /var/lib/apt/lists/*


# Clone the official Langflow repository and check out the desired branch/version.
RUN git clone https://github.com/langflow-ai/langflow.git . && \
    git checkout -b dev-dodao v1.1.4.dev13

# Install Python dependencies using uv.
# (Since the repository already contains pyproject.toml and uv.lock, we use them directly.)
RUN uv sync --frozen --no-install-project --no-editable

# Increase Node.js heap size to 8GB (adjust if needed)
ENV NODE_OPTIONS=--max-old-space-size=16384

# Build the frontend assets:
# Change to the frontend directory, install npm dependencies, build the assets,
# and copy the build output to the backend’s static folder.
WORKDIR /app/src/frontend
RUN npm ci && npm run build && \
    cp -r build /app/src/backend/langflow/frontend

# Return to the project root and sync the environment again.
WORKDIR /app
RUN uv sync --frozen --no-install-project --no-editable

################################
# RUNTIME STAGE
################################
# Use a slim Python 3.12.3 image for the runtime.
FROM python:3.12.3-slim AS runtime

# Update packages, install git, and create a non‑root user.
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y git && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    useradd user -u 1000 -g 0 --no-create-home --home-dir /app/data

# Copy the virtual environment from the builder stage.
COPY --from=builder --chown=1000 /app/.venv /app/.venv

# Prepend the virtual environment's bin directory to the PATH.
ENV PATH="/app/.venv/bin:$PATH"

# Set image metadata.
LABEL org.opencontainers.image.title="langflow" \
      org.opencontainers.image.authors="Langflow" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.url="https://github.com/langflow-ai/langflow" \
      org.opencontainers.image.source="https://github.com/langflow-ai/langflow"

# Switch to the non‑root user.
USER user

# Set the working directory and environment variables for Langflow.
WORKDIR /app
ENV LANGFLOW_HOST=0.0.0.0
ENV LANGFLOW_PORT=7860

# Expose port 7860.
EXPOSE 7860

# Start Langflow using the provided command.
CMD ["langflow", "run"]
