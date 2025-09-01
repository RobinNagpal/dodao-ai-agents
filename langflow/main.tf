terraform {
  required_version = ">= 1.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.54.1"
    }
  }
}

# Your existing default region provider
provider "aws" {
  region = var.aws_region
}

# Add: CloudFront needs the cert in us-east-1
provider "aws" {
  alias  = "virginia"
  region = "us-east-1"
}
