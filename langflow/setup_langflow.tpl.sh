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

# Install Nginx (without Certbot)
apt-get install -y nginx

# Clone the dodao-ai-agents repository
if [ ! -d "/home/ubuntu/dodao-ai-agents" ]; then
  git clone https://github.com/RobinNagpal/dodao-ai-agents.git /home/ubuntu/dodao-ai-agents
fi

# Create required directories
mkdir -p /home/ubuntu/dodao-ai-agents/langflow-bundles/{flows,components}
chown -R ubuntu:ubuntu /home/ubuntu/dodao-ai-agents

# Create Docker container
docker run -d --name langflow \\
  --restart unless-stopped \\
  -e LANGFLOW_AUTO_LOGIN=False \\
  -e LANGFLOW_SUPERUSER="${langflow_superuser}" \\
  -e LANGFLOW_SUPERUSER_PASSWORD="${langflow_superuser_password}" \\
  -e LANGFLOW_SECRET_KEY="${langflow_secret_key}" \\
  -e LANGFLOW_DATABASE_URL="${postgres_url}" \\
  -e OPENAI_API_KEY="${openai_api_key}" \\
  -e LANGFLOW_LOAD_FLOWS_PATH=/app/custom_flows \\
  -e LANGFLOW_COMPONENTS_PATH=/app/custom_components \\
  -v /home/ubuntu/dodao-ai-agents/langflow-bundles/custom_flows:/app/custom_flows \\
  -v /home/ubuntu/dodao-ai-agents/langflow-bundles/custom_components:/app/custom_components \\
  -p 127.0.0.1:7860:7860 \\
  public.ecr.aws/p7g4h0z9/langflow-public:latest

# Create SSL certificate directories
mkdir -p /etc/letsencrypt/live/${langflow_domain}
cat <<CERT_EOF > /etc/letsencrypt/live/${langflow_domain}/cert.pem
${cert_pem}
CERT_EOF

cat <<CHAIN_EOF > /etc/letsencrypt/live/${langflow_domain}/chain.pem
${chain_pem}
CHAIN_EOF

cat <<FULLCHAIN_EOF > /etc/letsencrypt/live/${langflow_domain}/fullchain.pem
${fullchain_pem}
FULLCHAIN_EOF

cat <<PRIVKEY_EOF > /etc/letsencrypt/live/${langflow_domain}/privkey.pem
${privkey_pem}
PRIVKEY_EOF

# Configure Nginx for HTTPS
rm -f /etc/nginx/sites-enabled/*
cat <<NGINX_EOF > /etc/nginx/sites-available/langflow
server {
  listen 80;
  server_name ${langflow_domain};
  return 301 https://\\\$host\\\$request_uri;
}

server {
  listen 443 ssl;
  server_name ${langflow_domain};

  ssl_certificate /etc/letsencrypt/live/${langflow_domain}/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/${langflow_domain}/privkey.pem;

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
nginx -t
systemctl restart nginx

echo -e "[\$(date)] Docker setup completed successfully"
SCRIPT_EOF
# Make the setup script executable and run it
chmod +x /home/ubuntu/scripts/setup_langflow.sh

# Create the update script for pulling the latest repo and restarting the container
cat <<UPDATE_EOF > /home/ubuntu/scripts/update_langflow.sh
#!/bin/bash
set -e
export DEBIAN_FRONTEND=noninteractive

LOG_FILE="/home/ubuntu/logs/update.log"
exec > >(tee -a "\$LOG_FILE") 2>&1

echo -e "\n[\$(date)] Starting update: pulling latest Git changes..."
cd /home/ubuntu/dodao-ai-agents
git pull

echo -e "\n[\$(date)] Restarting the Langflow container..."
docker restart langflow

echo -e "\n[\$(date)] Update completed successfully."
UPDATE_EOF

# Make the update script executable
chmod +x /home/ubuntu/scripts/update_langflow.sh

# Run the setup script
/home/ubuntu/scripts/setup_langflow.sh
