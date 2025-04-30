# Langflow Docker & AWS Deployment Setup

This repository provides a comprehensive guide to running Langflow with custom components using Docker and deploying it on AWS Lightsail via Terraform. Whether you're working in local development or setting up production infrastructure, this guide covers everything from building the Docker image to configuring AWS services, managing deployments, and automating updates.

---

## Table of Contents
- [Overview](#overview)
- [Langflow Docker Setup](#langflow-docker-setup)
- [Building the Docker Image](#building-the-docker-image)
- [AWS Lightsail Deployment](#aws-lightsail-deployment)
- [Deployment Overview](#deployment-overview)
- [Deployment Flow](#deployment-flow)
- [Terraform Configuration](#terraform-configuration)
- [Service Management & Debugging](#service-management--debugging)
- [Docker Image Management & Makefile Commands](#docker-image-management--makefile-commands)
- [Scripts and Automation](#scripts-and-automation)
- [Troubleshooting & Additional Resources](#troubleshooting--additional-resources)
- [Contributing](#contributing)

---

## Overview

This repository combines an custom(latest version of langflow) Docker setup for Langflow with a production-grade deployment 
on AWS Lightsail. It offers clear instructions for local development and production, including automated SSL provisioning, 
reverse proxy configuration, and service management.

---

## Langflow Docker Setup
We use LightSail instance and then install docker in it. We could have used LightSail's container service, but the current
setup is a bit cheaper.

So we
1. Create LightSail Instance
2. Install Docker in it
3. Run Langflow container
4. Install Nginx to expose the container to the internet

## Setup Process
We do the setup using terraform. `lightsail.tf` is the main file which has the setup code. In `lightsail.tf`, we create
a script which is run on the instance. This script installs docker, pulls the latest langflow image, and runs it.

We also install Nginx in the instance and configure it to forward requests to the langflow container.

Then we also create an update script which pulls the latest langflow image and restarts the container.

See `setup_langflow.tpl.sh` for more details.

## Building the Docker Image

We build the latest version(tag - v1.1.4.dev13) of langflow. We then build it and push it to AWS ECR. This image
is then pulled in docker on the LightSail instance, and we run the langflow container.

See the Dockerfile for more details.

## Custom Components
We install custom components in the langflow container. These components are mounted in the container. We clone
this repo on LightSail instance and then mount the components in the container.

When a new component is added, we can just pull the latest changes from the repo and restart the container.

This can be done via running `/home/ubuntu/scripts/update_langflow.sh` script.

## Testing Custom Components
You can either straight away create a new custom component in langflow and copy the code in the text area, or you can
also setup langflow on your local and test the component there. Setting on local is the recommended way.

The setup on local can be done by running `docker-compose up` in the `langflow-bundles` directory


## AWS Lightsail Deployment

### Deployment Overview

Deploy Langflow on an AWS Lightsail instance configured via Terraform. This setup uses:
- An Ubuntu instance (e.g., `ubuntu_24_04`) with ports for SSH (22), HTTP (80), and HTTPS (443).
- A Route 53 A-record mapping your domain (e.g., `langflow.dodao.io`) to the instance’s public IP.
- A startup script (provided through the `user_data` field) that installs dependencies, sets up Docker and Nginx, provisions SSL certificates, and configures a systemd service for Langflow.

### Deployment Flow

1. **Terraform Provisioning:**
    - The Lightsail instance is created with the required blueprint, bundle, and key pair.
    - Public ports are configured and a DNS record is created using Route 53.

2. **Instance Boot-Up:**
    - On boot, the instance executes the `user_data` script, logging progress to `/home/ubuntu/logs/setup.log`.

3. **Service Setup:**
    - A systemd service (`/etc/systemd/system/langflow.service`) is configured to manage Langflow.
    - The service is enabled and started automatically.

### Terraform Configuration

Here’s an excerpt of the Terraform configuration:
```hcl
data "template_file" "setup_langflow" {
  template = file("setup_langflow.tpl.sh")
  vars = {
    langflow_superuser         = var.langflow_superuser
    langflow_superuser_password = var.langflow_superuser_password
    langflow_secret_key        = var.langflow_secret_key
    postgres_url               = var.postgres_url
    openai_api_key             = var.openai_api_key
    langflow_domain            = "langflow.dodao.io"
    cert_pem                   = file("./langflow.dodao.io/cert1.pem")
    chain_pem                  = file("./langflow.dodao.io/chain1.pem")
    fullchain_pem              = file("./langflow.dodao.io/fullchain1.pem")
    privkey_pem                = file("./langflow.dodao.io/privkey1.pem")
  }
}

resource "aws_lightsail_instance" "langflow_docker_instance" {
  name              = "langflow-docker-instance"
  availability_zone = var.aws_availability_zone
  blueprint_id      = var.instance_blueprint_id
  bundle_id         = var.instance_bundle_id
  key_pair_name     = var.lightsail_key_pair
  user_data         = data.template_file.setup_langflow.rendered

  tags = {
    Environment = "Production"
    Application = "Langflow-Docker"
  }
}

resource "aws_lightsail_instance_public_ports" "langflow_docker_ports" {
  instance_name = aws_lightsail_instance.langflow_docker_instance.name

  port_info {
    from_port = 22
    to_port   = 22
    protocol  = "tcp"
  }

  port_info {
    from_port = 80
    to_port   = 80
    protocol  = "tcp"
  }

  port_info {
    from_port = 443
    to_port   = 443
    protocol  = "tcp"
  }
}
```
And a Route 53 record is set up as follows:
```hcl
data "aws_route53_zone" "primary" {
  name         = "dodao.io"
  private_zone = false
}

resource "aws_route53_record" "langflow_docker_dns" {
  zone_id = data.aws_route53_zone.primary.zone_id
  name    = "langflow.dodao.io"
  type    = "A"
  ttl     = 300
  records = [aws_lightsail_instance.langflow_docker_instance.public_ip_address]
}
```

### Service Management & Debugging

**During Initial Setup:**  
Monitor the setup log:
```bash
tail -f /home/ubuntu/logs/setup.log
```

**After Deployment:**  
Use these commands to manage the Langflow service:
- **Start the Service:**
  ```bash
  sudo systemctl start langflow.service
  ```
- **Stop the Service:**
  ```bash
  sudo systemctl stop langflow.service
  ```
- **Restart the Service:**
  ```bash
  sudo systemctl restart langflow.service
  ```
- **Check Status:**
  ```bash
  sudo systemctl status langflow.service
  ```
- **View Logs:**
  ```bash
  docker logs --tail 100 -f langflow
  ```

---

## Docker Image Management & Makefile Commands

For building, running, and pushing Docker images, a Makefile is provided. Below are the key commands:

```makefile
# Variables for Docker image name, repository, and port number.
IMAGE_NAME = langflow
PORT = 7860
REPO = 729763663166.dkr.ecr.us-east-1.amazonaws.com/langflow

# Build the Docker image.
build:
	@echo "Building the Docker image '$(IMAGE_NAME)'..."
	docker build -t $(IMAGE_NAME) .

# Run the Docker container.
run:
	@echo "Running the Docker container on port $(PORT)..."
	docker run -p $(PORT):7860 $(IMAGE_NAME)

# Rebuild the Docker image without cache.
rebuild:
	@echo "Rebuilding the Docker image '$(IMAGE_NAME)' without cache..."
	docker build --no-cache -t $(IMAGE_NAME) .

# Stop running Docker containers.
stop:
	@echo "Stopping the running Docker container(s) for '$(IMAGE_NAME)'..."
	docker stop $$(docker ps -q --filter "ancestor=$(IMAGE_NAME)")

# Tag and push the image to the ECR repository.
push: build
	@echo "Tagging the Docker image with the ECR repository '$(REPO)'..."
	aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 729763663166.dkr.ecr.us-east-1.amazonaws.com
	docker tag $(IMAGE_NAME) $(REPO)
	@echo "Pushing the Docker image to the ECR repository..."
	docker push $(REPO)

# Push the Docker image to Docker Hub.
push-to-docker:
	@echo "Pushing the Docker image to Docker Hub..."
	docker login
	docker tag $(IMAGE_NAME) robinnagpal/$(IMAGE_NAME)
	docker push robinnagpal/$(IMAGE_NAME)

# Push the Docker image to the public ECR.
push-to-ecr:
	@echo "Pushing the Docker image to ECR..."
	aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws/p7g4h0z9
	docker tag $(IMAGE_NAME) public.ecr.aws/p7g4h0z9/langflow-public:latest
	docker push public.ecr.aws/p7g4h0z9/langflow-public:latest

# Restart the Docker container via remote update.
restart-docker:
	chmod 600 ./LightsailDefaultKey-us-east-1.pem
	ssh -i ./LightsailDefaultKey-us-east-1.pem ubuntu@<lightsail-instance-public-ip> "/home/ubuntu/scripts/update_langflow.sh"
```

---

## Scripts and Automation

Two primary scripts help automate deployment and updates:

- **Setup Script (`setup_langflow.sh`):**
    - Runs on instance boot (via the `user_data` field).
    - Installs OS updates, Docker, Nginx, and other dependencies.
    - Clones the `dodao-ai-agents` repository, creates necessary directories, and starts the Langflow Docker container.
    - Configures SSL certificates and Nginx as a reverse proxy.

- **Update Script (`update_langflow.sh`):**
    - Pulls the latest changes from the Git repository.
    - Restarts the Langflow container to apply updates.

Both scripts log their output to `/home/ubuntu/logs/` for easier troubleshooting.

---

## Troubleshooting & Additional Resources

- **Log Files:**
    - Setup logs: `/home/ubuntu/logs/setup.log`
    - Update logs: `/home/ubuntu/logs/update.log`

- **Service Management:**  
  Use the provided systemd commands to start, stop, or restart the Langflow service.

- **Docker Issues:**  
  Verify that Docker is installed correctly and that the current user is added to the Docker group.

- **AWS Lightsail:**  
  Check instance configurations and network settings if you experience connectivity issues.

For more details, refer to the specific sections in this README or open an issue on the repository.

---

## Contributing

Contributions to improve the deployment process or add new features are welcome! Please submit issues or pull requests as appropriate.
