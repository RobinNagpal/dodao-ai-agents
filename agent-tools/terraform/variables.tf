variable "region" {
  type    = string
  default = "us-east-1"
}

variable "sec_edgar_image_uri" {
  type        = string
  description = "ECR image URI for the sec-edgar Lambda container"
}

variable "scrapingant_image_uri" {
  type        = string
  description = "ECR image URI for the scrapingant Lambda container"
}

variable "lambda_role_arn" {
  type        = string
  description = "ARN of the IAM role that the Lambda functions will assume"
}
