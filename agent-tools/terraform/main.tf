provider "aws" {
  region = var.region
}

# Example: If you need to create ECR repositories, you could do so here
# resource "aws_ecr_repository" "sec_edgar_repo" {
#   name = "sec-edgar"
# }
# resource "aws_ecr_repository" "scrapingant_repo" {
#   name = "scrapingant"
# }

resource "aws_lambda_function" "sec_edgar" {
  function_name = "sec-edgar"
  package_type  = "Image"
  image_uri     = var.sec_edgar_image_uri
  role          = var.lambda_role_arn
}

resource "aws_lambda_function" "scrapingant" {
  function_name = "scrapingant"
  package_type  = "Image"
  image_uri     = var.scrapingant_image_uri
  role          = var.lambda_role_arn
}
