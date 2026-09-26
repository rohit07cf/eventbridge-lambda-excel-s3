# =============================================================================
# main.tf — Local values and cross-cutting data sources
# =============================================================================

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

locals {
  # Consistent prefix for every resource name, e.g. "cost-report-dev".
  name_prefix = "${var.project_name}-${var.environment}"

  lambda_function_name = "${local.name_prefix}-cost-report"

  # Log group the Lambda runtime writes to; used to scope the IAM policy.
  lambda_log_group_arn = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${local.lambda_function_name}"

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}
