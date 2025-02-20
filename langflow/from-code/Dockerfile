# Use Python 3.11 slim image as the base for a lightweight environment.
FROM python:3.11-slim

# Set environment variables:
# - PYTHONDONTWRITEBYTECODE: Avoids writing .pyc files to disk.
# - PYTHONUNBUFFERED: Sends logs straight to the terminal.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Update package lists and install essential tools:
# - curl: To download installation scripts (e.g., for Node.js).
# - build-essential: Provides compilers and build tools.
# - git: Needed to clone the Langflow repository.
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    git

# Install Node.js (v18.x) by fetching and running the NodeSource setup script.
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs

# Install the 'uv' package via pip (required to run Langflow with uv).
RUN pip install uv

# Set the working directory to /app.
WORKDIR /app

# Clone the Langflow repository from GitHub into the working directory.
RUN git clone https://github.com/langflow-ai/langflow.git .

RUN git checkout -b dev-dodao v1.1.4.dev13
# Prepare the development environment by installing backend and frontend dependencies,
# and building the frontend static files. This mimics "make init" without starting the server.
# Increase Node.js heap size to 8GB (adjust if needed)
ENV NODE_OPTIONS=--max-old-space-size=8192

RUN make install_backend
RUN make install_frontend
RUN make build_frontend

# Expose port 7860 (the default port on which Langflow runs).
EXPOSE 7860

# Start Langflow using uv when the container runs.
CMD ["uv", "run", "langflow", "run"]
