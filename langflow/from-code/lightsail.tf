data "template_file" "setup_langflow" {
  template = file("setup_langflow.tpl.sh")
  vars = {
    certbot_email             = var.certbot_email
    langflow_superuser        = var.langflow_superuser
    langflow_superuser_password = var.langflow_superuser_password
    langflow_secret_key       = var.langflow_secret_key
    postgres_url              = var.postgres_url
    openai_api_key            = var.openai_api_key
    langflow_domain           = "langflow.dodao.io"  # Updated domain
  }
}

resource "aws_lightsail_instance" "langflow_docker_instance" {  # Changed resource name
  name              = "langflow-docker-instance"  # Changed instance name
  availability_zone = var.aws_availability_zone
  blueprint_id      = var.instance_blueprint_id
  bundle_id         = var.instance_bundle_id
  key_pair_name     = var.lightsail_key_pair
  user_data         = data.template_file.setup_langflow.rendered

  tags = {
    Environment = "Production"
    Application = "Langflow-Docker"  # Updated tag
  }
}

resource "aws_lightsail_instance_public_ports" "langflow_docker_ports" {  # Changed resource name
  instance_name = aws_lightsail_instance.langflow_docker_instance.name  # Updated reference

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

# Updated Route53 record
resource "aws_route53_record" "langflow_dns" {
  zone_id = data.aws_route53_zone.primary.zone_id
  name    = "langflow"  # Changed to match new domain
  type    = "A"
  ttl     = 300
  records = [aws_lightsail_instance.langflow_docker_instance.public_ip_address]  # Updated reference
}

##########################################################
# 4. Route53 DNS Record (langflow.dodao.io)              #
##########################################################
# Assumes you already have a Route53 hosted zone for dodao.io
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

##################################################
# 5. Variables (same as before but references)   #
##################################################
variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region to deploy into."
}

variable "aws_availability_zone" {
  type        = string
  default     = "us-east-1a"
  description = "AWS availability zone for the Lightsail instance."
}

variable "instance_blueprint_id" {
  type        = string
  default     = "ubuntu_24_04"
  description = "Blueprint ID for the Lightsail instance."
}

variable "instance_bundle_id" {
  type        = string
  default     = "medium_3_0"
  description = "Bundle ID for the Lightsail instance."
}

variable "lightsail_key_pair" {
  type        = string
  description = "Key pair name for SSH access to the Lightsail instance (optional)."
  default     = ""
}

variable "postgres_url" {
  type        = string
  sensitive   = true
  description = "URL for your existing Postgres database."
}

variable "langflow_superuser" {
  type        = string
  description = "Username for Langflow superuser."
}

variable "langflow_superuser_password" {
  type        = string
  sensitive   = true
  description = "Password for Langflow superuser."
}

variable "langflow_secret_key" {
  type        = string
  default     = "replace_with_generated_key"
  sensitive   = true
  description = "Secret key used by Langflow to encrypt sensitive data."
}

variable "openai_api_key" {
  type        = string
  sensitive   = true
  description = "API key for OpenAI."
}

variable "certbot_email" {
  type        = string
  description = "Email address for Let's Encrypt notifications."
  default     = "robinnagpal.tiet@gmail.com"
}
