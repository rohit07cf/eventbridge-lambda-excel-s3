# Requirements — EventBridge Lambda Excel S3

## Overview

This document defines the functional and non-functional requirements for an AWS-based
scheduled reporting workflow. The system uses Amazon EventBridge to trigger an AWS Lambda
function on a fixed schedule. The Lambda generates an Excel cost-report workbook in memory
and uploads it to Amazon S3. All infrastructure is provisioned and managed using Terraform.

---

## 1. Scheduling Requirements

### REQ-1.1 — EventBridge Schedule

The system must use Amazon EventBridge to trigger the Lambda function automatically
on a recurring schedule.

**Acceptance Criteria:**
- An EventBridge scheduled rule exists and is in the `ENABLED` state.
- The rule fires the Lambda every 5 minutes by default.
- The default schedule expression is `rate(5 minutes)`.

### REQ-1.2 — Configurable Schedule

The EventBridge schedule expression must be configurable through a Terraform variable
and must not be hardcoded directly in any Terraform resource.

**Acceptance Criteria:**
- A Terraform variable named `schedule_expression` exists with a default value of
  `"rate(5 minutes)"`.
- Overriding the variable changes the EventBridge rule without any other code modifications.
- The schedule expression supports both `rate()` and `cron()` syntax.

---

## 2. Lambda Requirements

### REQ-2.1 — Runtime and Handler

The Lambda function must be implemented in Python. The entry point must be
`lambda_function.lambda_handler`.

**Acceptance Criteria:**
- The Lambda runtime is `python3.12` (or the latest stable Python runtime available).
- The handler attribute is set to `lambda_function.lambda_handler`.

### REQ-2.2 — Handler Thinness

The Lambda handler must remain thin. It must orchestrate the workflow by calling
discrete modules rather than containing inline business logic.

**Acceptance Criteria:**
- `lambda_function.py` contains no Excel-generation logic.
- `lambda_function.py` contains no raw data definitions.
- Business logic lives in `data_provider.py` and `excel_generator.py`.

### REQ-2.3 — Environment Variables

The Lambda function must read all environment-specific configuration from environment
variables. No bucket names or infrastructure identifiers may be hardcoded in Python source.

**Acceptance Criteria:**
- The Lambda reads the S3 bucket name from the `OUTPUT_BUCKET` environment variable.
- If `OUTPUT_BUCKET` is absent or empty the Lambda raises a descriptive `EnvironmentError`
  before attempting any S3 interaction.

### REQ-2.4 — Lambda Compute Configuration

The Lambda function must have appropriate memory and timeout settings supplied as
Terraform variables.

**Acceptance Criteria:**
- Default memory is `256` MB.
- Default timeout is `30` seconds.
- Both values can be overridden via Terraform variables without modifying resource blocks.

### REQ-2.5 — Return Value

On successful execution the Lambda handler must return a structured JSON-serialisable
dictionary.

**Acceptance Criteria:**
- The return value contains `status`, `bucket`, `key`, and `rows_processed` fields.
- Example:
  ```json
  {
    "status": "success",
    "bucket": "example-bucket",
    "key": "processed/cost-report-2026-09-26-140500.xlsx",
    "rows_processed": 6
  }
  ```

---

## 3. Data Provider Requirements

### REQ-3.1 — Dummy Data Provider

The system must include a `data_provider.py` module that returns exactly six rows of
cost-report data. This is the initial implementation; no external data integrations
are required now.

**Acceptance Criteria:**
- `data_provider.py` exports a callable `get_report_data()` that returns a list of dicts.
- The list contains exactly six rows.
- Each row includes the fields: `item`, `location`, and one key per month
  (`jan_2026` through `sep_2026`).

### REQ-3.2 — Required Items

The six report items must be:

| Item                      | Location   |
|---------------------------|------------|
| SQL LTC                   | US-East    |
| AWS ARR                   | US-East    |
| AWS FIRE                  | US-West    |
| SQL Health Supp/Retire    | On-Prem    |
| Azure Filer (All)         | Azure-East |
| Filer (All)               | Global     |

**Acceptance Criteria:**
- All six item names appear in the returned data exactly as listed above.
- Locations match the values in the table above.

### REQ-3.3 — Monthly Cost Values

Each row must include numeric cost values for January 2026 through September 2026
(nine months total).

**Acceptance Criteria:**
- All nine monthly values in every row are positive integers or floats.
- Values are plausible cloud/IT cost figures (roughly in the range 5,000–25,000).
- Values exhibit realistic month-on-month variation (not all identical).

### REQ-3.4 — Extensibility Contract

The data provider must expose a stable interface so that the dummy implementation can
later be replaced by integrations with Flexera, Apptio, AXIS, or S3-sourced files
without modifying `excel_generator.py` or `lambda_function.py`.

**Acceptance Criteria:**
- `get_report_data()` returns a `list[dict]` with a documented, stable schema.
- No external-integration code is implemented at this stage.

---

## 4. Excel Generation Requirements

### REQ-4.1 — Library

The Excel workbook must be generated using the `openpyxl` Python library.

**Acceptance Criteria:**
- `openpyxl` is listed in `src/requirements.txt`.
- No other Excel library is introduced.

### REQ-4.2 — Worksheet Name

The workbook must contain a single worksheet named exactly `Cost Report`.

**Acceptance Criteria:**
- `wb.sheetnames` returns `["Cost Report"]` (only one sheet, correct name).

### REQ-4.3 — Column Headers

The worksheet must contain the following eleven columns in order:

```
Item | Location | Jan 2026 | Feb 2026 | Mar 2026 | Apr 2026 |
May 2026 | Jun 2026 | Jul 2026 | Aug 2026 | Sep 2026
```

**Acceptance Criteria:**
- Row 1 of the worksheet contains exactly these eleven header values.
- Column order matches the sequence above.

### REQ-4.4 — Data Rows

The worksheet must contain exactly six data rows (rows 2–7), one per item from the
data provider.

**Acceptance Criteria:**
- `ws.max_row` equals `7` (1 header + 6 data rows).
- Each data row contains the item name, location, and nine numeric monthly values.

### REQ-4.5 — Professional Formatting

The workbook must include basic professional formatting. Over-engineering styling
is explicitly out of scope.

**Acceptance Criteria:**
- Header row cells are **bold**.
- Header row is frozen (freeze panes set at `A2`).
- AutoFilter is enabled on the header row.
- Column widths are set to readable values (not default narrow widths).
- Monthly cost columns use a numeric or currency-style number format.
- The data range is formatted as an Excel Table (using `openpyxl.worksheet.table.Table`).

### REQ-4.6 — In-Memory Generation

The workbook must be generated entirely in memory using `io.BytesIO`. The Lambda
must not write the Excel file to the local filesystem unless technically unavoidable.

**Acceptance Criteria:**
- `excel_generator.py` returns a `BytesIO` object containing the workbook bytes.
- No `tempfile` or `/tmp` writes are used.

---

## 5. S3 Requirements

### REQ-5.1 — Bucket Provisioning

An S3 bucket must be created and managed entirely by Terraform.

**Acceptance Criteria:**
- A `aws_s3_bucket` resource is defined in Terraform.
- The bucket name is derived from Terraform variables (e.g., `project_name` and
  `environment`).
- No S3 bucket is created manually or outside Terraform.

### REQ-5.2 — Public Access Block

The S3 bucket must block all public access.

**Acceptance Criteria:**
- An `aws_s3_bucket_public_access_block` resource is attached to the bucket.
- All four block settings (`block_public_acls`, `block_public_policy`,
  `ignore_public_acls`, `restrict_public_buckets`) are set to `true`.

### REQ-5.3 — Object Key Pattern

Every uploaded Excel file must use a timestamped key under the `processed/` prefix.

**Acceptance Criteria:**
- Object key follows the pattern `processed/cost-report-YYYY-MM-DD-HHMMSS.xlsx`.
- The timestamp is generated dynamically at Lambda execution time using UTC.
- Two executions that start in different seconds produce different object keys.

### REQ-5.4 — Upload Mechanism

The Lambda must upload the in-memory `BytesIO` workbook directly to S3 using the
AWS SDK (`boto3`).

**Acceptance Criteria:**
- `boto3` is used for the S3 upload.
- The upload uses `put_object` or `upload_fileobj`.
- The object is not written to disk before uploading.

---

## 6. Terraform Requirements

### REQ-6.1 — Single Source of Truth

All AWS infrastructure must be defined in Terraform. No AWS resources for this project
may be created through the console, CLI, or any other mechanism.

**Acceptance Criteria:**
- All resources (S3, IAM, Lambda, EventBridge) have corresponding Terraform resource
  definitions.
- `terraform plan` on a clean account shows only expected resources.

### REQ-6.2 — File Structure

The Terraform configuration must follow a clean multi-file layout.

**Acceptance Criteria:**
- The `terraform/` directory contains at minimum:
  `providers.tf`, `variables.tf`, `main.tf`, `s3.tf`, `iam.tf`,
  `lambda.tf`, `eventbridge.tf`, `outputs.tf`.
- Each file has a clearly documented responsibility.

### REQ-6.3 — Provider Configuration

The AWS provider must be configurable via a Terraform variable for region.

**Acceptance Criteria:**
- A variable `aws_region` exists with a sensible default (e.g., `"us-east-1"`).
- The provider block references `var.aws_region`.

### REQ-6.4 — Variables

The Terraform configuration must define variables for all values that are likely to
change between environments or deployments.

**Acceptance Criteria:**
- Variables defined at minimum: `aws_region`, `environment`, `project_name`,
  `schedule_expression`, `lambda_memory_size`, `lambda_timeout`.
- All variables include a `description` and appropriate `type`.
- Variables that require user input have no default; variables with universal defaults
  carry one.

### REQ-6.5 — Outputs

The Terraform configuration must expose useful outputs for operators.

**Acceptance Criteria:**
- Outputs defined at minimum: `s3_bucket_name`, `lambda_function_name`,
  `eventbridge_rule_name`.
- All outputs include a `description`.

---

## 7. IAM Requirements

### REQ-7.1 — Lambda Execution Role

A dedicated IAM role must be created for the Lambda function following least-privilege
principles.

**Acceptance Criteria:**
- An `aws_iam_role` with an `AssumeRolePolicyDocument` allowing
  `lambda.amazonaws.com` to assume the role is defined.
- No other principal is listed in the assume-role policy.

### REQ-7.2 — CloudWatch Logs Permissions

The Lambda execution role must allow the Lambda to write logs to CloudWatch.

**Acceptance Criteria:**
- The role has permissions for `logs:CreateLogGroup`, `logs:CreateLogStream`,
  and `logs:PutLogEvents`.
- Permissions are scoped to the relevant log group ARN where possible.

### REQ-7.3 — S3 Least-Privilege

The Lambda execution role must allow only the minimum S3 permissions required.

**Acceptance Criteria:**
- The role grants `s3:PutObject` only.
- The resource is scoped to the target bucket ARN and the `processed/*` prefix
  (e.g., `arn:aws:s3:::bucket-name/processed/*`).
- `s3:GetObject`, `s3:DeleteObject`, and broader permissions are not granted.
- Wildcard actions (`"*"`) are not used.

### REQ-7.4 — EventBridge Lambda Invocation Permission

EventBridge must be granted permission to invoke the Lambda function.

**Acceptance Criteria:**
- An `aws_lambda_permission` resource allows `events.amazonaws.com` as the principal.
- The permission is scoped to the specific EventBridge rule ARN as the `source_arn`.

---

## 8. Logging Requirements

### REQ-8.1 — Structured Logging

The Lambda must emit structured, human-readable log messages at key points in execution.

**Acceptance Criteria:**
- The following events are logged at the `INFO` level as a minimum:
  1. Lambda execution started
  2. EventBridge invocation received
  3. Report data generation started
  4. Number of report rows generated
  5. Excel generation started
  6. Excel generation completed
  7. Target S3 bucket
  8. Target S3 object key
  9. S3 upload started
  10. S3 upload completed
  11. Lambda execution completed
- Python's built-in `logging` module is used (not `print`).

### REQ-8.2 — Exception Logging

All unhandled exceptions must be caught, logged with sufficient context for
troubleshooting, and then re-raised so that Lambda marks the invocation as failed.

**Acceptance Criteria:**
- A top-level `try/except` block in the handler logs exception type, message, and
  stack trace using `logger.exception(...)`.
- The exception is re-raised after logging so the Lambda execution is recorded as
  a failure in CloudWatch.

---

## 9. Dependency Packaging Requirements

### REQ-9.1 — Lambda ZIP Package

`openpyxl` and its dependencies are not part of the standard Lambda Python runtime
and must be bundled into the deployment package.

**Acceptance Criteria:**
- A packaging script `scripts/package_lambda.sh` produces a ZIP file containing
  the Lambda source files and all dependencies from `src/requirements.txt`.
- The resulting ZIP can be used directly as the Terraform Lambda deployment package.

### REQ-9.2 — Excluded Artefacts

Generated build artefacts must not be committed to the repository.

**Acceptance Criteria:**
- `.gitignore` excludes `*.zip`, `lambda_package/`, `build/`, `dist/`.
- The packaging script outputs to a location that is `.gitignore`d.

---

## 10. Testing Requirements

### REQ-10.1 — Unit Tests for Excel Generator

The Excel-generation logic must be independently unit-testable without any AWS
dependency.

**Acceptance Criteria:**
- `tests/test_excel_generator.py` exists and passes with `pytest`.
- Tests do not import `boto3` or require AWS credentials.

### REQ-10.2 — Required Test Cases

The test suite must cover at minimum:

| ID    | Test                                                        |
|-------|-------------------------------------------------------------|
| T-01  | Workbook can be generated successfully (no exceptions)      |
| T-02  | Worksheet is named `Cost Report`                            |
| T-03  | All eleven required columns are present                     |
| T-04  | Exactly six data rows exist                                 |
| T-05  | All six expected item names are present in column A         |
| T-06  | Jan 2026 through Sep 2026 column headers are present        |
| T-07  | All monthly cost values in every data row are numeric       |
| T-08  | The `BytesIO` output can be loaded by `openpyxl.load_workbook` |

---

## 11. Repository Structure Requirements

### REQ-11.1 — Directory Layout

The repository must follow the agreed structure.

**Acceptance Criteria:**
- The following paths exist:
  ```
  src/lambda_function.py
  src/data_provider.py
  src/excel_generator.py
  src/requirements.txt
  tests/test_excel_generator.py
  terraform/providers.tf
  terraform/variables.tf
  terraform/main.tf
  terraform/s3.tf
  terraform/iam.tf
  terraform/lambda.tf
  terraform/eventbridge.tf
  terraform/outputs.tf
  scripts/package_lambda.sh
  README.md
  .gitignore
  ```

### REQ-11.2 — .gitignore

The repository must include a `.gitignore` that excludes generated and sensitive files.

**Acceptance Criteria:**
- The following patterns are excluded at minimum:
  `.terraform/`, `*.tfstate`, `*.tfstate.*`, `.terraform.lock.hcl`,
  `__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `.env`,
  `build/`, `dist/`, `lambda_package/`, `*.zip`,
  `.idea/`, `.vscode/`.
- AWS credential files are not committed.

---

## 12. Non-Functional Requirements

### REQ-12.1 — Simplicity

The architecture must not introduce AWS services beyond those required:
EventBridge, Lambda, S3, IAM, CloudWatch Logs.

**Acceptance Criteria:**
- No API Gateway, DynamoDB, Step Functions, ECS, Glue, RDS, SNS, or SQS resources
  are defined in Terraform or referenced in application code.

### REQ-12.2 — Maintainability

Code must follow separation-of-concerns principles. Python modules must have single,
clearly defined responsibilities.

**Acceptance Criteria:**
- `data_provider.py` is responsible only for supplying report data.
- `excel_generator.py` is responsible only for workbook creation.
- `lambda_function.py` is responsible only for orchestration and AWS interactions.

### REQ-12.3 — Configuration Over Hardcoding

No infrastructure identifiers, bucket names, region strings, or schedule expressions
may appear as string literals in Python application code.

**Acceptance Criteria:**
- All such values are sourced from environment variables at runtime.
- Python code uses `os.environ` to read configuration.

### REQ-12.4 — Type Hints

Python modules should use type hints on public function signatures to aid
readability and IDE tooling.

**Acceptance Criteria:**
- `get_report_data()`, `generate_excel()`, and `lambda_handler()` carry type annotations.

### REQ-12.5 — Future Extensibility

The data-provider layer must be designed so that the dummy implementation can be
swapped for a real data source (Flexera, Apptio, AXIS, S3 input) without modifying
the Excel generator or Lambda handler.

**Acceptance Criteria:**
- The data-provider interface (`get_report_data()`) is documented.
- A comment or docstring in `data_provider.py` describes the stable return schema.
- No tight coupling exists between `data_provider.py` and `excel_generator.py`
  beyond the agreed list-of-dicts interface.
