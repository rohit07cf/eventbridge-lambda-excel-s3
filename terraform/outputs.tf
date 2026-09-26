# =============================================================================
# outputs.tf — Operator-facing outputs (see design.md §10.3)
# =============================================================================

output "s3_bucket_name" {
  description = "Name of the S3 bucket that receives Excel cost reports"
  value       = aws_s3_bucket.reports.bucket
}

output "lambda_function_name" {
  description = "Name of the Lambda function that generates cost reports"
  value       = aws_lambda_function.cost_report.function_name
}

output "eventbridge_rule_name" {
  description = "Name of the EventBridge scheduled rule"
  value       = aws_cloudwatch_event_rule.schedule.name
}
