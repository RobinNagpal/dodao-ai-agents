#!/bin/bash
set -e
export DEBIAN_FRONTEND=noninteractive

# Create directories for scripts and logs
mkdir -p /home/ubuntu/scripts /home/ubuntu/logs
chown ubuntu:ubuntu /home/ubuntu/logs

# Create the setup script with logging
cat <<SCRIPT_EOF > /home/ubuntu/scripts/setup_langflow.sh
#!/bin/bash
set -e
export DEBIAN_FRONTEND=noninteractive

LOG_FILE="/home/ubuntu/logs/setup.log"
exec > >(tee -a "\$LOG_FILE") 2>&1
echo -e "\n[\$(date)] Starting Langflow Docker setup"

# Update and install dependencies
apt-get update -y
apt-get install -y apt-transport-https ca-certificates curl software-properties-common

# Install Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io
usermod -aG docker ubuntu

# Install Nginx and Certbot
apt-get install -y nginx certbot python3-certbot-nginx

# Clone the dodao-ui repository
if [ ! -d "/home/ubuntu/dodao-ui" ]; then
  git clone https://github.com/RobinNagpal/dodao-ui.git /home/ubuntu/dodao-ui
fi

# Create required directories
mkdir -p /home/ubuntu/dodao-ui/ai-agents/langflow-flows/langflow-bundles/{flows,components}
chown -R ubuntu:ubuntu /home/ubuntu/dodao-ui

# Create Docker container
docker run -d --name langflow \\
  --restart unless-stopped \\
  -e LANGFLOW_AUTO_LOGIN=False \\
  -e LANGFLOW_SUPERUSER="${langflow_superuser}" \\
  -e LANGFLOW_SUPERUSER_PASSWORD="${langflow_superuser_password}" \\
  -e LANGFLOW_SECRET_KEY="${langflow_secret_key}" \\
  -e LANGFLOW_DATABASE_URL="${postgres_url}" \\
  -e OPENAI_API_KEY="${openai_api_key}" \\
  -e LANGFLOW_LOAD_FLOWS_PATH=/app/flows \\
  -e LANGFLOW_COMPONENTS_PATH=/app/components \\
  -v /home/ubuntu/dodao-ui/ai-agents/langflow-flows/langflow-bundles/flows:/app/flows \\
  -v /home/ubuntu/dodao-ui/ai-agents/langflow-flows/langflow-bundles/components:/app/components \\
  -p 127.0.0.1:7860:7860 \\
  public.ecr.aws/p7g4h0z9/langflow-public:latest

# Configure Nginx
rm -f /etc/nginx/sites-enabled/*
cat <<NGINX_EOF > /etc/nginx/sites-available/langflow
server {
  listen 80;
  server_name ${langflow_domain};
  location / {
    proxy_pass http://127.0.0.1:7860;
    proxy_set_header Host $$host;
    proxy_set_header X-Real-IP $$remote_addr;
    proxy_set_header X-Forwarded-For $$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $$scheme;
  }
}
NGINX_EOF

ln -s /etc/nginx/sites-available/langflow /etc/nginx/sites-enabled/
systemctl restart nginx

# Obtain SSL certificate
max_retries=5
retry_count=0
until [ \$retry_count -ge \$max_retries ]; do
  certbot --nginx --non-interactive --agree-tos --redirect -m ${certbot_email} -d ${langflow_domain} && break
  retry_count=\$((retry_count + 1))
  sleep 60
done


echo -e "[\$(date)] Docker setup completed successfully"
SCRIPT_EOF

# Make the setup script executable and run it
chmod +x /home/ubuntu/scripts/setup_langflow.sh
/home/ubuntu/scripts/setup_langflow.sh
