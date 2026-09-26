"""
lambda_function.py
------------------
AWS Lambda entry point for the scheduled cost-report workflow.

Single responsibility: orchestrate the workflow — read configuration,
call the data provider, call the Excel generator, upload the result to S3,
and return a structured result.  No data definitions or Excel logic live here.

Workflow (triggered every 5 minutes by Amazon EventBridge):
    1. Read OUTPUT_BUCKET from environment variables.
    2. Call data_provider.get_report_data() → list[dict]
    3. Call excel_generator.generate_excel(rows)  → BytesIO
    4. Build a timestamped S3 object key.
    5. Upload the workbook to S3 via boto3.
    6. Return a structured result dict.

Environment variables
---------------------
OUTPUT_BUCKET : str  (required)
    Name of the S3 bucket to which the generated Excel file is uploaded.
    Supplied by Terraform via the Lambda ``environment`` block — never
    hardcoded in this file.

Return value (success)
----------------------
{
    "status":         "success",
    "bucket":         "<bucket-name>",
    "key":            "processed/cost-report-YYYY-MM-DD-HHMMSS.xlsx",
    "rows_processed": 6
}
"""

import logging
import os
from datetime import datetime, timezone
from io import BytesIO

import boto3

from data_provider import get_report_data
from excel_generator import generate_excel

# ---------------------------------------------------------------------------
# Logger — Lambda automatically ships stdout/stderr to CloudWatch Logs.
# No handler configuration is required; the Lambda runtime attaches one.
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Content-type for the uploaded XLSX object so S3 serves it correctly.
_XLSX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


def lambda_handler(event: dict, context) -> dict:
    """Handle an EventBridge scheduled invocation.

    Parameters
    ----------
    event : dict
        The EventBridge event payload.  The handler does not rely on any
        field from this payload; it is accepted for API compatibility.
    context : LambdaContext
        Lambda runtime context object (not used directly).

    Returns
    -------
    dict
        Structured result with keys: status, bucket, key, rows_processed.

    Raises
    ------
    EnvironmentError
        If the required OUTPUT_BUCKET environment variable is absent or empty.
    Exception
        Any unhandled exception is logged with its full traceback and re-raised
        so that Lambda marks the invocation as FAILED in CloudWatch metrics.
    """
    logger.info("Lambda execution started")
    logger.info("EventBridge invocation received")

    try:
        # ------------------------------------------------------------------
        # 1. Read required configuration from environment
        # ------------------------------------------------------------------
        bucket_name: str = os.environ.get("OUTPUT_BUCKET", "").strip()
        if not bucket_name:
            raise EnvironmentError(
                "Required environment variable OUTPUT_BUCKET is not set or is empty. "
                "Ensure the Lambda function's environment block contains OUTPUT_BUCKET."
            )

        # ------------------------------------------------------------------
        # 2. Fetch report data
        # ------------------------------------------------------------------
        logger.info("Report data generation started")
        rows: list[dict] = get_report_data()
        logger.info("Generated %d report rows", len(rows))

        # ------------------------------------------------------------------
        # 3. Generate Excel workbook in memory
        # ------------------------------------------------------------------
        logger.info("Excel generation started")
        workbook_buffer: BytesIO = generate_excel(rows)
        logger.info("Excel generation completed")

        # ------------------------------------------------------------------
        # 4. Build timestamped S3 object key (UTC)
        # ------------------------------------------------------------------
        timestamp: str = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
        s3_key: str = f"processed/cost-report-{timestamp}.xlsx"

        logger.info("Target S3 bucket: %s", bucket_name)
        logger.info("Target S3 key: %s", s3_key)

        # ------------------------------------------------------------------
        # 5. Upload workbook to S3
        # ------------------------------------------------------------------
        s3_client = boto3.client("s3")
        logger.info("S3 upload started")
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=workbook_buffer.getvalue(),
            ContentType=_XLSX_CONTENT_TYPE,
        )
        logger.info("S3 upload completed")

        # ------------------------------------------------------------------
        # 6. Return structured result
        # ------------------------------------------------------------------
        result: dict = {
            "status": "success",
            "bucket": bucket_name,
            "key": s3_key,
            "rows_processed": len(rows),
        }
        logger.info("Lambda execution completed successfully")
        return result

    except Exception:
        # Log the full traceback so CloudWatch contains enough detail to
        # diagnose the failure, then re-raise so Lambda records a FAILED
        # invocation in CloudWatch metrics.
        logger.exception("Unhandled exception during execution")
        raise
