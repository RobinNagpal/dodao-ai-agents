##############################
# AWS and Lightsail Settings
##############################
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
  default     = "ubuntu_24_04"  # Adjust as needed
  description = "Blueprint ID for the Lightsail instance."
}

variable "instance_bundle_id" {
  type        = string
  default     = "medium_3_0"    # Adjust based on performance/cost requirements
  description = "Bundle ID for the Lightsail instance."
}

variable "lightsail_key_pair" {
  type        = string
  default     = ""              # Set your SSH key pair name if used
  description = "Key pair name for SSH access to the Lightsail instance."
}

##############################
# Langflow and Application Settings
##############################
variable "postgres_url" {
  type        = string
  sensitive   = true
  description = "URL for your Postgres database."
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
  description = "API key for OpenAI (if needed)."
}

variable "certbot_email" {
  type        = string
  default     = "youremail@gmail.com"
  description = "Email address for Let's Encrypt notifications."
}

##############################
# Docker & Deployment Settings
##############################
variable "image_tag" {
  type        = string
  default     = "latest"
  description = "The tag of the Docker image to deploy."
}

variable "aws_account_id" {
  type        = string
  description = "AWS Account ID."
}

variable "langflow_domain" {
  type        = string
  description = "Domain name for Langflow."
}
