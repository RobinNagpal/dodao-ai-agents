# Define variables for the Docker image name, repository, and port number.
IMAGE_NAME = langflow
PORT = 7860
REPO = 729763663166.dkr.ecr.us-east-1.amazonaws.com/langflow

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

# The 'push' target tags and pushes the Docker image to the ECR repository.
push: build
	@echo "Tagging the Docker image with the ECR repository '$(REPO)'..."
	aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 729763663166.dkr.ecr.us-east-1.amazonaws.com
	docker tag $(IMAGE_NAME) $(REPO)
	@echo "Pushing the Docker image to the ECR repository..."
	docker push $(REPO)

push-to-docker:
	@echo "Pushing the Docker image to Docker Hub..."
	docker login
	docker tag $(IMAGE_NAME) robinnagpal/$(IMAGE_NAME)
	docker push robinnagpal/$(IMAGE_NAME)

push-to-ecr:
	@echo "Pushing the Docker image to ECR..."
	aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws/p7g4h0z9
	docker tag $(IMAGE_NAME) public.ecr.aws/p7g4h0z9/langflow-public:latest
	docker push public.ecr.aws/p7g4h0z9/langflow-public:latest

restart-docker:
	chmod 600 ./LightsailDefaultKey-us-east-1.pem
	ssh -i ./LightsailDefaultKey-us-east-1.pem ubuntu@<lightsail-instance-public-ip> "/home/ubuntu/scripts/update_langflow.sh"
