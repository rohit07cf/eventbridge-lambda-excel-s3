# =============================================================================
# variables.tf — Input variable declarations (see design.md §10.2)
# =============================================================================

variable "aws_region" {
  type        = string
  description = "AWS region for all resources"
  default     = "us-east-1"
}

variable "environment" {
  type        = string
  description = "Deployment environment (e.g. dev, prod)"
}

variable "project_name" {
  type        = string
  description = "Project identifier used in resource names"
}

variable "schedule_expression" {
  type        = string
  description = "EventBridge schedule expression that triggers the Lambda"
  default     = "rate(5 minutes)"
}

variable "lambda_memory_size" {
  type        = number
  description = "Lambda memory in MB"
  default     = 256
}

variable "lambda_timeout" {
  type        = number
  description = "Lambda timeout in seconds"
  default     = 30
}
