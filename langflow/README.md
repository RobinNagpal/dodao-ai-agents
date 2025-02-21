# Updating Deployment
Rightnow we deploy langflow to AWS Lightsail instance. Below you will see all the instructions to deploy langflow to AWS Lightsail instance.

We now want to update the deployment and use docker within the AWS Lightsail instance. So the langflow image will 
be built and pushed to AWS ECR and then pulled and installed in the AWS Lightsail instance.

We are doing this because we want to run the latest code of langflow on our environment.

Things we want to achieve:
- [x] We want to run the latest code of langflow on our environment.
    - [x] Build the docker image of langflow.
    - [ ] Ignore for now - We want to run it in a way so that it uses our database. For this we need to pass the database url 
       to the docker container as environment variable. `LANGFLOW_DATABASE_URL`.
    - [ ] Ignore for now - Along with this we can pass other environment variables as well.
- [ ] We want to run and install the custom components in langflow. Langflow has a feature to install custom components and mention the path of the custom components in environment variable `LANGFLOW_CUSTOM_COMPONENTS_PATH`.
    - [ ] Do this - We want to mount the local directory to a path in the docker container. This path(the path in container) will be used as the `LANGFLOW_CUSTOM_COMPONENTS_PATH`.
    - [ ] Do this - Make sure the custom components show up in the langflow UI.

Some clarifications:
- We will not be using docker-compose. We will be using docker only.
- Docker Compose is used to run multiple containers. We will be running only one container, so we will be using docker only.
- Docker can be used to run a single container and pass environment variables to it. And also to mount volumes.
- Hassaan doesn't need to do anything with lightsail instance. 
- No need to push as well.


### How will the new deployment work?
Here are the following pieces of the deployment:
1. Docker Container
   - This will be build using the latest code of langflow.
   - We will then push this image to our AWS ECR.
2. AWS Lightsail Instance
   - Lightsail instance is like a normal linux server. We will use this to run the docker container.
   - Just like we run the docker container on our local machine, we will run the docker container on the AWS Lightsail instance.
   - We will pull the latest image from AWS ECR and run the docker container on the AWS Lightsail instance.
3. Custom Components
   - Our custom components are stored in `dodao-ai-agents` repository. We will clone this reporitory on the AWS Lightsail instance, or on your local machine and 
     then mount this directory to the docker container.
   - So we dont need to clone the repo inside the docker container. We will clone it on the AWS Lightsail instance(or local) and then mount this directory to the docker container.
   - This way we just need to pull the latest code from the `dodao-ai-agents` repository, and restart the docker container to see the changes. The new custom components will be available in the docker container and the UI.

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
