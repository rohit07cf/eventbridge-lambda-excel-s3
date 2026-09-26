# =============================================================================
# lambda.tf — Cost-report Lambda function
# =============================================================================
# The deployment ZIP is built by scripts/package_lambda.sh, which writes
# lambda.zip to the repository root.  Run the script before `terraform plan`.
# =============================================================================

locals {
  lambda_zip_path = "${path.module}/../lambda.zip"
}

resource "aws_lambda_function" "cost_report" {
  function_name    = local.lambda_function_name
  role             = aws_iam_role.lambda_exec.arn
  runtime          = "python3.12"
  handler          = "lambda_function.lambda_handler"
  filename         = local.lambda_zip_path
  source_code_hash = filebase64sha256(local.lambda_zip_path)
  memory_size      = var.lambda_memory_size
  timeout          = var.lambda_timeout

  environment {
    variables = {
      OUTPUT_BUCKET = aws_s3_bucket.reports.bucket
    }
  }

  tags = local.common_tags

  # Ensure log permissions exist before the first invocation.
  depends_on = [aws_iam_role_policy.lambda_exec]
}
