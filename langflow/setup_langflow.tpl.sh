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

# Remove default site just in case
rm -f /etc/nginx/sites-enabled/* /etc/nginx/sites-available/default

# Helper maps (keep $ variables intact by single-quoting the heredoc)
cat >/etc/nginx/conf.d/proto_map.conf <<'MAPEOF'
map $$http_cloudfront_forwarded_proto $$xfp {
    default $$http_cloudfront_forwarded_proto;
    ""      $$scheme;
}
map $$http_upgrade $$connection_upgrade {
    default upgrade;
    ""      close;
}
MAPEOF

# Actual site config (single-quoted heredoc!)
cat >/etc/nginx/sites-available/langflow <<'NGINX_EOF'
server {
  listen 80 default_server;
  server_name origin-langflow.dodao.io langflow.dodao.io;

  # health endpoint
  location /health {
    add_header Content-Type text/plain;
    return 200 'ok';
  }

  # Langflow app on localhost:7860
  location / {
    proxy_http_version 1.1;

    # WebSockets
    proxy_set_header Upgrade $$http_upgrade;
    proxy_set_header Connection $$connection_upgrade;

    proxy_pass http://127.0.0.1:7860;

    # standard proxy headers
    proxy_set_header Host $$host;
    proxy_set_header X-Real-IP $$remote_addr;
    proxy_set_header X-Forwarded-For $$proxy_add_x_forwarded_for;

    # reflect viewer protocol if CloudFront supplied it, else use $$scheme
    proxy_set_header X-Forwarded-Proto $$xfp;
    proxy_set_header X-Forwarded-Host $$host;
  }
}
NGINX_EOF

ln -sf /etc/nginx/sites-available/langflow /etc/nginx/sites-enabled/langflow
nginx -t && systemctl reload nginx



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
