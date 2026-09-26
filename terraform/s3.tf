# =============================================================================
# s3.tf — Report bucket (private, SSE-S3 encrypted, public access blocked)
# =============================================================================

resource "aws_s3_bucket" "reports" {
  # Must be globally unique across all AWS accounts.
  bucket = "${local.name_prefix}-reports"

  tags = local.common_tags
}

resource "aws_s3_bucket_public_access_block" "reports" {
  bucket = aws_s3_bucket.reports.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "reports" {
  bucket = aws_s3_bucket.reports.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
