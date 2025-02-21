# Langflow Docker Setup

This repository provides a Docker setup for running [Langflow](https://github.com/langflow-ai/langflow) with **custom components**.

## Requirements
- [Docker](https://docs.docker.com/get-docker/) installed
- [Git](https://git-scm.com/) (for cloning repositories if needed)

## 1. Directory Structure

Make sure your custom components reside in a folder hierarchy like:
```
custom_components/
    tools/
        my_tool.py
    helpers/
        helper_component.py
```
> The folder under `custom_components` (e.g., `tools`, `helpers`) **determines the category name** in Langflow’s UI.

## 2. Building the Docker Image

Place or clone the Langflow repo (or a Dockerfile that references it) in a folder, then build:

```bash
docker build -t langflow-custom .
```

This creates a Docker image named `langflow-custom`.

## 3. Running the Container (Volume-Mount Approach)

### Local Development

You can **mount** your local `custom_components` folder into the container so that changes appear without rebuilding the image:

```bash
docker run -p 7860:7860 -v "<your_custom_components_path_in_local>:/app/custom_components" langflow-custom
```

### Verify Components
Inside the container, you can check your files were mounted correctly:
```bash
docker exec -it <container_id> ls /app/custom_components
```
You should see subfolders (`tools`, `helpers`, etc.) and `.py` files.

## 4. Alternative: Copy Components Into Image

For **production** deployments or if you prefer a self-contained image, you can **copy** the components into the Docker image:

1. Put your `custom_components/` folder in the same directory as your Dockerfile.
2. Add this snippet in your `Dockerfile`:
   ```dockerfile
   COPY custom_components /app/custom_components
   ENV LANGFLOW_COMPONENTS_PATH=/app/custom_components
   ```
3. Build and run **without** mounting a volume:
   ```bash
   docker build -t langflow-custom .
   docker run -p 7860:7860 langflow-custom
   ```

Your custom components will be in the image itself, so no extra volume mapping is required.
