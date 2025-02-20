# Define variables for the Docker image name and the port number.
IMAGE_NAME = langflow
PORT = 7860

# The 'build' target builds the Docker image using the Dockerfile.
build:
	@echo "Building the Docker image '$(IMAGE_NAME)'..."
	docker build -t $(IMAGE_NAME) .

# The 'run' target runs the Docker container, mapping container port 7860 to local port 7860.
run:
	@echo "Running the Docker container on port $(PORT)..."
	docker run -p $(PORT):7860 $(IMAGE_NAME)

# The 'rebuild' target forces a rebuild of the Docker image without using cache.
rebuild:
	@echo "Rebuilding the Docker image '$(IMAGE_NAME)' without cache..."
	docker build --no-cache -t $(IMAGE_NAME) .

# The 'stop' target stops any running container created from the image.
stop:
	@echo "Stopping the running Docker container(s) for '$(IMAGE_NAME)'..."
	docker stop $$(docker ps -q --filter "ancestor=$(IMAGE_NAME)")
