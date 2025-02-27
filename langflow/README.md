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


# Deployment Guide: Langflow on AWS Lightsail
This guide explains how the Lightsail instance is configured to run Langflow using Terraform and a startup script. It also covers the main commands used for service management, debugging, and viewing logs.

### Overview

- **Infrastructure:**  
  A Lightsail instance is created using Terraform. The instance is provisioned with Ubuntu (using a blueprint such as `ubuntu_24_04`) and assigned public ports (SSH: 22, HTTP: 80, HTTPS: 443). A Route 53 A-record is set up to map your domain (e.g., `langflow-ai.dodao.io`) to the instance’s public IP.

- **Setup Script:**  
  A shell script (`setup_langflow.sh`) is deployed via the Lightsail `user_data` field. This script:
    - Updates the OS and installs required packages (Python, pip, Nginx, Certbot, etc.)
    - Configures Nginx as a reverse proxy to Langflow running on port 7860.
    - Uses Certbot to obtain an SSL certificate (with automatic retry logic).
    - Sets up a Python virtual environment and installs Langflow.
    - Configures and enables a systemd service for Langflow.

### Deployment Flow

1. **Terraform Configuration:**
    - The Terraform code provisions the Lightsail instance with the correct blueprint, bundle, key pair, and public port settings.
    - A Route 53 DNS record is created so that your domain points to the instance.

2. **Instance Boot-Up:**
    - When the instance boots, the provided `user_data` runs the setup script.
    - The script logs its progress to `/home/ubuntu/logs/setup.log`.

3. **Service Setup:**
    - The Langflow service is defined via a systemd unit (`/etc/systemd/system/langflow.service`).
    - The service is enabled and started automatically.

### Service Management and Debugging Commands

##### During Initial Setup
you can monitor the logs to check the progress of the setup script:

```bash
tail -f /home/ubuntu/logs/setup.log
```

##### Post-Deployment
After deployment, you can manage and debug the Langflow service using the following commands:

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

- **Check Service Status:**

  ```bash
  sudo systemctl status langflow.service
  ```

- **View Logs via systemd (journalctl):**

  ```bash
  sudo journalctl -u langflow.service -f
  ```

  This command is a shortcut to quickly view the Langflow service logs.

### Terraform Variables

The Terraform configuration makes use of several variables for customization. Some key variables include:

- `certbot_email`: Email address for Let's Encrypt notifications.
- `langflow_superuser` and `langflow_superuser_password`: Credentials for the Langflow superuser.
- `langflow_secret_key`: Secret key used for encryption.
- `postgres_url`: URL for the Postgres database.
- `openai_api_key`: API key for OpenAI.
- `instance_blueprint_id` and `instance_bundle_id`: Define the Lightsail instance type.
- `lightsail_key_pair`: SSH key pair name for access.
- `aws_availability_zone`: The AWS zone (e.g., `us-east-1a`).
- `langflow_domain`: Domain name used in the Nginx configuration and Certbot setup.

### Summary

This setup deploys Langflow on an AWS Lightsail instance with automated SSL provisioning, Nginx reverse proxy configuration, and a dedicated systemd service. Use the commands listed above to start, stop, or debug the service as needed.
