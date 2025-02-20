#!/bin/bash
set -e
export DEBIAN_FRONTEND=noninteractive

# Create directories for scripts and logs
mkdir -p /home/ubuntu/scripts /home/ubuntu/logs
chown ubuntu:ubuntu /home/ubuntu/logs

cat <<'SCRIPT_EOF' > /home/ubuntu/scripts/setup_langflow.sh
#!/bin/bash
set -e
export DEBIAN_FRONTEND=noninteractive

# Redirect output to log file
LOG_FILE="/home/ubuntu/logs/setup.log"
exec > >(tee -a "$LOG_FILE") 2>&1
echo -e "\n[$(date)] Starting Langflow Docker setup"

# Update OS and install required packages (including Docker and AWS CLI)
apt-get update -y
apt-get install -y docker.io awscli nginx certbot python3-certbot-nginx

# Start and enable Docker service
systemctl start docker
systemctl enable docker

# Configure Nginx as reverse proxy (HTTP configuration)
rm -f /etc/nginx/sites-enabled/*
cat <<NGINX_EOF > /etc/nginx/sites-available/langflow
server {
  listen 80;
  server_name ${langflow_domain};
  location / {
    proxy_pass http://127.0.0.1:7860;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
  }
}
NGINX_EOF

ln -s /etc/nginx/sites-available/langflow /etc/nginx/sites-enabled/
systemctl restart nginx

# Obtain SSL certificate with retries
max_retries=5
retry_count=0
until [ $retry_count -ge $max_retries ]; do
  certbot --nginx --non-interactive --agree-tos --redirect -m ${certbot_email} -d ${langflow_domain} && break
  retry_count=$((retry_count + 1))
  sleep 60
done

# Log in to AWS ECR and pull the Langflow Docker image
REGION="${aws_region}"
DOCKER_REGISTRY="${aws_account_id}.dkr.ecr.${aws_region}.amazonaws.com"
IMAGE_TAG="${image_tag}"
aws ecr get-login-password --region ${aws_region} | docker login --username AWS --password-stdin ${DOCKER_REGISTRY}

echo "Pulling Docker image ${DOCKER_REGISTRY}/langflow:${IMAGE_TAG}"
docker pull $${DOCKER_REGISTRY}/langflow:$${IMAGE_TAG}

# Stop and remove any existing container named 'langflow'
if docker ps -a --format '{{.Names}}' | grep -Eq "^langflow\$"; then
  docker stop langflow
  docker rm langflow
fi

# Run the Docker container
docker run -d --name langflow -p 7860:7860 \
  -e LANGFLOW_SUPERUSER=${langflow_superuser} \
  -e LANGFLOW_SUPERUSER_PASSWORD=${langflow_superuser_password} \
  -e LANGFLOW_SECRET_KEY=${langflow_secret_key} \
  -e LANGFLOW_DATABASE_URL=${postgres_url} \
  -e OPENAI_API_KEY=${openai_api_key} \
  -e LANGFLOW_LOAD_FLOWS_PATH=/home/ubuntu/dodao-ui/ai-agents/langflow-flows/langflow-bundles/flows \
  -e LANGFLOW_COMPONENTS_PATH=/home/ubuntu/dodao-ui/ai-agents/langflow-flows/langflow-bundles/components \
  $${DOCKER_REGISTRY}/langflow:$${IMAGE_TAG}

echo "[$(date)] Langflow Docker container started successfully"
SCRIPT_EOF

# Make the setup script executable and run it
chmod +x /home/ubuntu/scripts/setup_langflow.sh
/home/ubuntu/scripts/setup_langflow.sh
