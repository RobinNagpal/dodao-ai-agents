# Use official Python base image
FROM python:3.10-slim

# Set environment variables
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV DO_NOT_TRACK=true
ENV LANGFLOW_COMPONENTS_PATH=/app/custom_components

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    make \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js and yarn
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g yarn

# Install uv (Python package manager)
RUN pip install uv

# Clone Langflow repository into the working directory
RUN git clone https://github.com/langflow-ai/langflow.git .

# Checkout the custom branch for dodao
RUN git checkout -b dev-dodao v1.1.4.dev13

# Run the individual build commands (without starting the server)
RUN make install_backend && \
    make install_frontend && \
    make build_frontend

# Expose Langflow's default port
EXPOSE 7860

# Set the container's entrypoint to run the server binding to all interfaces
CMD ["uv", "run", "langflow", "run", "--host", "0.0.0.0"]
