output "sec_edgar_lambda_arn" {
  description = "ARN of the sec-edgar Lambda function"
  value       = aws_lambda_function.sec_edgar.arn
}

output "scrapingant_lambda_arn" {
  description = "ARN of the scrapingant Lambda function"
  value       = aws_lambda_function.scrapingant.arn
}
