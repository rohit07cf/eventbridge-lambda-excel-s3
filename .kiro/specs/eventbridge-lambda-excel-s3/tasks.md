# Implementation Plan

## Overview

This document lists all implementation tasks grouped into thirteen phases. Tasks are
ordered so that each phase can be verified before the next begins. Work through the
phases sequentially; do not begin Phase N+1 until all tasks in Phase N are complete
and verified.

Each task maps to one or more requirements in `requirements.md` and one or more
design decisions in `design.md`. Cross-references are noted inline where helpful.

---

## Tasks

## Phase 1 — Repository Setup

Establish the directory structure, dependency files, and hygiene configuration
before writing any application logic.

- [x] Create the `src/` directory at the repository root.
- [x] Create the `tests/` directory at the repository root.
- [x] Create the `terraform/` directory at the repository root.
- [x] Create the `scripts/` directory at the repository root.
- [x] Create `src/requirements.txt` with `openpyxl>=3.1,<4.0` as the sole entry.
- [x] Create a root-level `requirements-dev.txt` with `pytest>=7.0` and `openpyxl>=3.1,<4.0`.
- [x] Create `.gitignore` at the repository root containing at minimum:
  ```
  # Terraform
  .terraform/
  *.tfstate
  *.tfstate.*
  .terraform.lock.hcl
  terraform.tfvars

  # Python
  __pycache__/
  *.pyc
  *.pyo
  .venv/
  venv/
  .env

  # Build artefacts
  build/
  dist/
  lambda_package/
  *.zip

  # IDE
  .idea/
  .vscode/

  # Secrets / credentials
  *.pem
  *.key
  credentials
  ```
- [x] Verify the `.gitignore` patterns cover all artefact types listed in REQ-11.2.
- [x] Confirm the directory layout matches the structure defined in `design.md` Section 13
  by running `find . -not -path './.git/*' -type d | sort`.

**Verification checkpoint:** The repository skeleton exists; no application files yet.

---

## Phase 2 — Data Provider

Implement the dummy data layer that supplies the six cost-report rows.

- [x] Create `src/data_provider.py` with a module-level docstring describing its purpose
  and the stable return schema (as defined in `design.md` Section 4.1).
- [x] Define the type alias or schema comment documenting the expected dict shape:
  `item`, `location`, `jan_2026` … `sep_2026`.
- [x] Implement `get_report_data() -> list[dict]` that returns a list of exactly six
  row dicts.
- [x] Add the row for **SQL LTC** with location `US-East` and nine numeric monthly
  values (Jan–Sep 2026) matching the dummy values in `design.md` Section 4.3.
- [x] Add the row for **AWS ARR** with location `US-East` and nine monthly values.
- [x] Add the row for **AWS FIRE** with location `US-West` and nine monthly values.
- [x] Add the row for **SQL Health Supp/Retire** with location `On-Prem` and nine
  monthly values.
- [x] Add the row for **Azure Filer (All)** with location `Azure-East` and nine
  monthly values.
- [x] Add the row for **Filer (All)** with location `Global` and nine monthly values.
- [x] Add type hints on the function signature (`-> list[dict]`).
- [x] Add a docstring to `get_report_data()` that references the stable interface
  contract and notes that this function is the correct place to substitute a real
  data integration (per REQ-3.4 and `design.md` Section 14.1).
- [x] Confirm all nine monthly values in every row are positive integers or floats
  (manual review).

**Verification checkpoint:** `python -c "from data_provider import get_report_data; rows = get_report_data(); assert len(rows) == 6; print('OK')"` exits cleanly from inside `src/`.

---

## Phase 3 — Excel Generator

Implement the Excel workbook generation module.

- [x] Create `src/excel_generator.py` with a module-level docstring describing its
  single responsibility (render a workbook from structured data; no AWS or data
  concerns).
- [x] Import `openpyxl`, `openpyxl.styles.Font`, `openpyxl.worksheet.table.Table`,
  `openpyxl.worksheet.table.TableStyleInfo`, and `io.BytesIO`.
- [x] Define the ordered list of column headers as a module-level constant:
  `["Item", "Location", "Jan 2026", "Feb 2026", "Mar 2026", "Apr 2026",
    "May 2026", "Jun 2026", "Jul 2026", "Aug 2026", "Sep 2026"]`
- [x] Define the ordered list of dict keys that map to those columns (per
  `design.md` Section 4.2).
- [x] Implement `generate_excel(rows: list[dict]) -> BytesIO`.
- [x] Inside `generate_excel`, create an `openpyxl.Workbook()` and set the active
  worksheet title to `"Cost Report"`.
- [x] Write the header row (row 1): iterate over the column header list and write
  each value to the correct cell.
- [x] Apply `Font(bold=True)` to every cell in the header row.
- [x] Write data rows (rows 2–7): for each row dict iterate over the key list and
  write the corresponding value to the worksheet.
- [x] Apply a numeric number format (e.g. `"#,##0.00"`) to cells in the cost columns
  (columns 3–11, i.e. Jan–Sep 2026) for all data rows.
- [x] Create an `openpyxl.worksheet.table.Table` with:
  - `displayName="CostReport"`
  - `ref` covering the full data range (`A1:K7`)
  - a `TableStyleInfo` (e.g. `TableStyleMedium9`, `showRowStripes=True`)
  - add the table to the worksheet via `ws.add_table(table)`.
- [x] Set freeze panes at cell `A2` (`ws.freeze_panes = "A2"`).
- [x] Set column width for column A (Item) to 28.
- [x] Set column width for column B (Location) to 14.
- [x] Set column widths for columns C–K (monthly cost columns) to 12 each.
- [x] Save the workbook to a `BytesIO` buffer: `wb.save(buffer)`.
- [x] Call `buffer.seek(0)` before returning.
- [x] Return the `BytesIO` buffer.
- [x] Add a docstring to `generate_excel()` describing inputs, outputs, and the
  assumption that rows conform to the schema in `design.md` Section 4.1.

**Verification checkpoint:** `python -c "from excel_generator import generate_excel; from data_provider import get_report_data; buf = generate_excel(get_report_data()); print('Bytes:', len(buf.getvalue()))"` prints a non-zero byte count from inside `src/`.

---

## Phase 4 — Unit Tests

Write the unit test suite for the Excel generator before completing the Lambda handler,
so correctness can be established independently of AWS.

- [x] Create `tests/test_excel_generator.py`.
- [x] Add the necessary imports: `pytest`, `openpyxl`, `BytesIO`, and both
  `get_report_data` / `generate_excel` from `src/`.
- [x] Add a module-level `@pytest.fixture` (or a helper) that calls
  `generate_excel(get_report_data())`, loads the returned `BytesIO` with
  `openpyxl.load_workbook()`, and yields the workbook — so all tests share one
  workbook instance.
- [x] **T-01** — Write a test asserting the workbook can be generated and loaded
  without raising any exception.
- [x] **T-02** — Write a test asserting `wb.sheetnames == ["Cost Report"]`.
- [x] **T-03** — Write a test asserting all eleven expected column headers are present
  in row 1 of the `Cost Report` worksheet.
- [x] **T-04** — Write a test asserting `ws.max_row == 7` (1 header + 6 data rows).
- [x] **T-05** — Write a test asserting all six expected item names appear in column A
  (cells A2:A7).
- [x] **T-06** — Write a test asserting that the nine month headers (Jan 2026 through
  Sep 2026) are present in the header row.
- [x] **T-07** — Write a test asserting every monthly cost value in every data row
  (columns 3–11, rows 2–7) is an `int` or `float` (i.e. numeric, not a string).
- [x] **T-08** — Write a test asserting the `BytesIO` object returned by
  `generate_excel()` can be loaded by `openpyxl.load_workbook()` without error
  (verifies the buffer is a valid XLSX file).
- [x] Ensure no test imports `boto3` or makes any network call.
- [x] Run `pytest tests/` from the repository root and confirm all eight tests pass.

**Verification checkpoint:** `pytest tests/ -v` shows 8 tests collected, 8 passed, 0 failed.

---

## Phase 5 — Lambda Handler

Implement the Lambda orchestrator that wires the data provider, Excel generator,
and S3 upload together.

- [x] Create `src/lambda_function.py`.
- [x] Add imports: `os`, `logging`, `boto3`, `datetime` / `timezone`, and
  `get_report_data` from `data_provider`, `generate_excel` from `excel_generator`.
- [x] Configure the module-level logger:
  ```python
  import logging
  logger = logging.getLogger(__name__)
  logger.setLevel(logging.INFO)
  ```
- [x] Implement `lambda_handler(event: dict, context) -> dict`.
- [x] At the very start of the handler, log `"Lambda execution started"` at INFO.
- [x] Log `"EventBridge invocation received"` at INFO.
- [x] Read `OUTPUT_BUCKET` from `os.environ`; raise an `EnvironmentError` with a
  descriptive message if the variable is absent or empty.
- [x] Log `"Report data generation started"` at INFO.
- [x] Call `get_report_data()` and store the result.
- [x] Log the number of rows returned (e.g. `f"Generated {len(rows)} report rows"`)
  at INFO.
- [x] Log `"Excel generation started"` at INFO.
- [x] Call `generate_excel(rows)` and store the returned `BytesIO` buffer.
- [x] Log `"Excel generation completed"` at INFO.
- [x] Build the timestamped S3 object key using UTC:
  ```python
  from datetime import datetime, timezone
  timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
  key = f"processed/cost-report-{timestamp}.xlsx"
  ```
- [x] Log the target bucket name at INFO.
- [x] Log the target S3 key at INFO.
- [x] Initialise a `boto3.client("s3")` instance.
- [x] Log `"S3 upload started"` at INFO.
- [x] Upload the workbook using `s3.put_object(Bucket=..., Key=..., Body=...,
  ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")`.
- [x] Log `"S3 upload completed"` at INFO.
- [x] Log `"Lambda execution completed successfully"` at INFO.
- [x] Construct and return the result dictionary:
  ```python
  {
      "status": "success",
      "bucket": bucket_name,
      "key": key,
      "rows_processed": len(rows),
  }
  ```
- [x] Wrap the entire workflow body (from reading `OUTPUT_BUCKET` to returning the
  result) in a `try/except Exception` block.
- [x] In the `except` block, call `logger.exception("Unhandled exception during execution")`
  and then `raise`.
- [x] Add a type-annotated function signature: `lambda_handler(event: dict, context) -> dict`.
- [x] Add a docstring to `lambda_handler` describing the expected EventBridge event
  and the return value schema.

**Verification checkpoint:** `python -c "import lambda_function"` completes without import errors from inside `src/`.

---

## Phase 6 — Lambda Dependency Packaging

Create the build script that produces the deployable Lambda ZIP artefact.

- [x] Create `scripts/package_lambda.sh` and make it executable (`chmod +x`).
- [x] Add a shebang line `#!/usr/bin/env bash` and `set -euo pipefail`.
- [x] Add a comment block at the top of the script explaining its purpose: it packages
  Lambda source and dependencies into a ZIP for Terraform deployment.
- [x] Add the step to remove any previous build directory: `rm -rf lambda_package/`.
- [x] Add the step to create a fresh build directory: `mkdir -p lambda_package/`.
- [x] Add the step to install Python dependencies into the build directory:
  ```bash
  pip install \
      -r src/requirements.txt \
      --target lambda_package/ \
      --platform manylinux2014_x86_64 \
      --only-binary=:all: \
      --quiet
  ```
- [x] Add the step to copy Lambda source files into the build directory:
  `cp src/lambda_function.py src/data_provider.py src/excel_generator.py lambda_package/`
- [x] Add the step to produce the ZIP:
  ```bash
  cd lambda_package
  zip -r ../lambda.zip . -x "*.pyc" -x "__pycache__/*"
  cd ..
  ```
- [x] Add a final echo confirming success: `echo "Lambda package ready: lambda.zip"`.
- [x] Confirm `lambda_package/` and `lambda.zip` are covered by `.gitignore` (already
  done in Phase 1 — verify).
- [x] Run `bash scripts/package_lambda.sh` from the repository root and confirm
  `lambda.zip` is created and contains `lambda_function.py`, `data_provider.py`,
  `excel_generator.py`, and `openpyxl/` (or its top-level files).
- [x] Verify `openpyxl` is present inside the ZIP:
  `unzip -l lambda.zip | grep openpyxl | head -5`.

**Verification checkpoint:** `lambda.zip` exists, is non-empty, and contains both source files and the `openpyxl` package.

---

## Phase 7 — Terraform: S3

Establish the Terraform project and provision the S3 bucket.

- [x] Create `terraform/providers.tf` declaring:
  - Terraform version constraint (e.g. `required_version = ">= 1.5"`).
  - The `hashicorp/aws` provider with a version constraint (e.g. `~> 5.0`).
  - The `aws` provider block referencing `var.aws_region`.
- [x] Create `terraform/variables.tf` with declarations (type + description + default
  where applicable) for:
  `aws_region`, `environment`, `project_name`, `schedule_expression`,
  `lambda_memory_size`, `lambda_timeout`.
  (At this phase, only `aws_region`, `environment`, and `project_name` need to be
  present; remaining variables will be referenced as later phases add resources.)
- [x] Create `terraform/main.tf` with a `locals` block defining a `name_prefix`
  local: `"${var.project_name}-${var.environment}"` for consistent resource naming.
- [x] Create `terraform/s3.tf` with an `aws_s3_bucket` resource named `reports`:
  - Terraform logical name: `reports` (referenced as `aws_s3_bucket.reports` elsewhere).
  - `bucket` set to `"${local.name_prefix}-reports"` (must be globally unique).
  - A `tags` map including at least `Project` and `Environment`.
- [x] Add an `aws_s3_bucket_public_access_block` resource in `terraform/s3.tf`:
  - `bucket` referencing `aws_s3_bucket.reports.id`.
  - All four blocking settings set to `true`.
- [x] Run `terraform init` inside `terraform/` and confirm it succeeds.
- [x] Run `terraform fmt -recursive terraform/` and confirm no formatting errors.
- [x] Run `terraform validate` inside `terraform/` and confirm no validation errors.

**Verification checkpoint:** `terraform validate` returns "Success! The configuration is valid."

---

## Phase 8 — Terraform: IAM

Create the Lambda execution role with least-privilege permissions.

- [x] Create `terraform/iam.tf`.
- [x] Add an `aws_iam_role` resource named `lambda_exec` for the Lambda execution role:
  - Terraform logical name: `lambda_exec` (referenced as `aws_iam_role.lambda_exec` elsewhere).
  - `name`: `"${local.name_prefix}-lambda-role"`.
  - Assume-role policy granting `sts:AssumeRole` to `lambda.amazonaws.com` only.
  - Tags.
- [x] Add an `aws_iam_role_policy` (inline policy) resource:
  - Name: `"${local.name_prefix}-lambda-policy"`.
  - Two statements:
    1. CloudWatch Logs: `logs:CreateLogGroup`, `logs:CreateLogStream`,
       `logs:PutLogEvents` scoped to the Lambda log group ARN.
    2. S3 PutObject: `s3:PutObject` scoped to
       `"${aws_s3_bucket.reports.arn}/processed/*"`.
  - No wildcard actions or resources.
- [x] Run `terraform validate` and confirm no errors.
- [x] Run `terraform plan` and review that IAM resources look correct (no unexpected
  wildcards in the diff).

**Verification checkpoint:** `terraform plan` shows the IAM role and policy with narrowly scoped permissions.

---

## Phase 9 — Terraform: Lambda

Define the Lambda function resource and wire it to the IAM role, S3 bucket, and
deployment package.

- [x] Add `schedule_expression`, `lambda_memory_size`, and `lambda_timeout` variable
  declarations to `terraform/variables.tf` if not already present (with defaults
  `"rate(5 minutes)"`, `256`, and `30` respectively).
- [x] Create `terraform/lambda.tf`.
- [x] Add a `data "archive_file"` resource (or use a direct `filename` attribute)
  referencing the packaging script output: `../lambda.zip` relative to the Terraform
  directory. Use `source_code_hash = filebase64sha256(...)` for change detection.
  - If using `data "archive_file"`, confirm the ZIP already exists before running
    `terraform plan` (run `scripts/package_lambda.sh` first).
- [x] Add an `aws_lambda_function` resource named `cost_report`:
  - Terraform logical name: `cost_report` (referenced as `aws_lambda_function.cost_report` elsewhere).
  - `function_name`: `"${local.name_prefix}-cost-report"`.
  - `role`: `aws_iam_role.lambda_exec.arn`.
  - `runtime`: `"python3.12"`.
  - `handler`: `"lambda_function.lambda_handler"`.
  - `filename` / `source_code_hash` referencing the ZIP.
  - `memory_size`: `var.lambda_memory_size`.
  - `timeout`: `var.lambda_timeout`.
  - `environment.variables`: `{ OUTPUT_BUCKET = aws_s3_bucket.reports.bucket }`.
  - Tags.
- [x] Run `terraform fmt -recursive terraform/` to check formatting.
- [x] Run `terraform validate` and confirm no errors.
- [x] Run `terraform plan` and verify the Lambda function appears with correct
  runtime, memory, timeout, and environment variable.

**Verification checkpoint:** `terraform plan` shows Lambda function with `python3.12` runtime and `OUTPUT_BUCKET` environment variable pointing to the S3 bucket.

---

## Phase 10 — Terraform: EventBridge

Configure the EventBridge schedule rule, Lambda target, and invocation permission.

- [x] Create `terraform/eventbridge.tf`.
- [x] Add an `aws_cloudwatch_event_rule` resource named `schedule`:
  - Terraform logical name: `schedule` (referenced as `aws_cloudwatch_event_rule.schedule` elsewhere).
  - `name`: `"${local.name_prefix}-schedule"`.
  - `description`: A meaningful description (e.g. `"Trigger cost report Lambda every 5 minutes"`).
  - `schedule_expression`: `var.schedule_expression`.
  - `state`: `"ENABLED"`.
  - Tags.
- [x] Add an `aws_cloudwatch_event_target` resource:
  - `rule`: referencing the rule above.
  - `target_id`: `"CostReportLambdaTarget"`.
  - `arn`: `aws_lambda_function.cost_report.arn`.
- [x] Add an `aws_lambda_permission` resource:
  - `statement_id`: `"AllowEventBridgeInvoke"`.
  - `action`: `"lambda:InvokeFunction"`.
  - `function_name`: `aws_lambda_function.cost_report.function_name`.
  - `principal`: `"events.amazonaws.com"`.
  - `source_arn`: `aws_cloudwatch_event_rule.schedule.arn`.
- [x] Run `terraform fmt -recursive terraform/`.
- [x] Run `terraform validate` and confirm no errors.
- [x] Run `terraform plan` and verify EventBridge rule shows `rate(5 minutes)` as
  the schedule expression.

**Verification checkpoint:** `terraform plan` shows EventBridge rule with `schedule_expression = "rate(5 minutes)"` and the Lambda permission scoped to the rule ARN.

---

## Phase 11 — Terraform: Outputs

Expose the key infrastructure identifiers as Terraform outputs.

- [x] Create `terraform/outputs.tf`.
- [x] Add output `s3_bucket_name`:
  - `value`: `aws_s3_bucket.reports.bucket`.
  - `description`: `"Name of the S3 bucket that receives Excel cost reports"`.
- [x] Add output `lambda_function_name`:
  - `value`: `aws_lambda_function.cost_report.function_name`.
  - `description`: `"Name of the Lambda function that generates cost reports"`.
- [x] Add output `eventbridge_rule_name`:
  - `value`: `aws_cloudwatch_event_rule.schedule.name`.
  - `description`: `"Name of the EventBridge scheduled rule"`.
- [x] Run `terraform validate` and confirm no errors.
- [x] Run `terraform plan` and confirm all three outputs appear in the plan output.

**Verification checkpoint:** `terraform plan` lists three outputs with correct sources and descriptions.

---

## Phase 12 — Documentation

Write the project README so that any engineer can set up, build, deploy, and verify
the system from scratch.

- [x] Open (or create) `README.md` and structure it with the following sections:
- [x] **Architecture** — describe the EventBridge → Lambda → Excel → S3 flow with
  a brief text diagram; reference `design.md` for full detail.
- [x] **Repository Structure** — show the directory tree from `design.md` Section 13.
- [x] **Prerequisites** — list required tools with minimum versions:
  Python 3.12+, pip, Terraform 1.5+, AWS CLI v2, bash.
- [x] **Installing Python dependencies (local development)**:
  ```bash
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements-dev.txt
  ```
- [x] **Running unit tests**:
  ```bash
  pytest tests/ -v
  ```
- [x] **Packaging the Lambda**:
  ```bash
  bash scripts/package_lambda.sh
  ```
- [x] **Terraform: initialise**:
  ```bash
  cd terraform
  terraform init
  ```
- [x] **Terraform: format check**:
  ```bash
  terraform fmt -recursive
  ```
- [x] **Terraform: validate**:
  ```bash
  terraform validate
  ```
- [x] **Terraform: plan**:
  ```bash
  terraform plan -var="environment=dev" -var="project_name=cost-report"
  ```
- [x] **Terraform: apply**:
  ```bash
  terraform apply -var="environment=dev" -var="project_name=cost-report"
  ```
- [x] **Manually invoking the Lambda**:
  ```bash
  aws lambda invoke \
    --function-name <lambda_function_name output> \
    response.json
  cat response.json
  ```
- [x] **Verifying S3 output**:
  ```bash
  aws s3 ls s3://<s3_bucket_name output>/processed/
  ```
- [x] **Checking CloudWatch Logs**:
  ```bash
  aws logs tail /aws/lambda/<lambda_function_name output> --follow
  ```
- [x] **Verifying EventBridge execution** — explain how to check the EventBridge
  rule metrics in the AWS console or via CloudWatch metrics.
- [x] **Terraform: destroy**:
  ```bash
  terraform destroy -var="environment=dev" -var="project_name=cost-report"
  ```
- [x] **Configuration reference** — table of all Terraform variables and Lambda
  environment variables.
- [x] Review the README for accuracy against the actual implementation before
  marking this task complete.

**Verification checkpoint:** README is readable top-to-bottom; all commands are syntactically correct and reference the correct resource names.

---

## Phase 13 — Validation

Final end-to-end validation pass before the implementation is considered complete.

### Code Quality

- [x] Run `pytest tests/ -v` and confirm all 8 tests pass with 0 failures.
- [x] Run `terraform fmt -check -recursive terraform/` and confirm no formatting
  issues are reported.
- [x] Run `terraform validate` inside `terraform/` and confirm "The configuration
  is valid."
- [x] Run `terraform plan -var="environment=dev" -var="project_name=cost-report"`
  and review the output for unexpected resources, missing variables, or policy errors.

### Packaging Verification

- [x] Re-run `bash scripts/package_lambda.sh` from a clean state (delete
  `lambda_package/` and `lambda.zip` first) and confirm the package is rebuilt
  successfully.
- [x] Confirm `lambda.zip` contains `lambda_function.py`, `data_provider.py`,
  `excel_generator.py`, and the `openpyxl` package directory.

### Requirement Cross-Check

- [x] **EventBridge → Lambda permission** — verify `aws_lambda_permission` resource
  exists in `terraform/eventbridge.tf` with `principal = "events.amazonaws.com"` and
  `source_arn` scoped to the EventBridge rule ARN.
- [x] **Lambda → S3 permission** — verify the IAM policy in `terraform/iam.tf`
  grants `s3:PutObject` only, scoped to `processed/*` on the target bucket.
- [x] **CloudWatch logging** — verify the IAM policy grants `logs:CreateLogGroup`,
  `logs:CreateLogStream`, `logs:PutLogEvents` and that the Lambda logger is
  configured in `lambda_function.py`.
- [x] **Lambda environment variables** — verify `OUTPUT_BUCKET` is set in the
  `aws_lambda_function` resource `environment` block and that `lambda_function.py`
  reads it via `os.environ`.
- [x] **Lambda dependency packaging** — verify `openpyxl` is present in `lambda.zip`
  and not in the Lambda runtime by default.
- [x] **Excel output correctness** — manually run the Excel generator against the
  data provider and open the resulting file (or inspect it via openpyxl) to confirm:
  - Worksheet named `Cost Report`.
  - 11 columns present.
  - 6 data rows.
  - Bold headers.
  - Freeze panes at A2.
  - Numeric formatting on cost columns.
- [x] **5-minute EventBridge schedule** — verify `schedule_expression` defaults to
  `"rate(5 minutes)"` in `terraform/variables.tf` and that the EventBridge rule
  resource references `var.schedule_expression` rather than a hardcoded string.
- [x] **No unnecessary AWS services** — confirm no API Gateway, DynamoDB, Step
  Functions, ECS, Glue, RDS, SNS, or SQS resources appear anywhere in `terraform/`.
- [x] **No hardcoded infrastructure values in Python** — grep the `src/` directory
  for any S3 bucket name literals or hardcoded region strings:
  ```bash
  grep -rn "us-east\|s3\.amazonaws\|arn:aws" src/
  ```
  Confirm the grep returns no matches.

**Verification checkpoint:** All checklist items above are confirmed. The project is ready for `terraform apply` and a live integration test.

---

## Task Dependency Graph

```
Phase 1 (Repository Setup)
  └── Phase 2 (Data Provider)
        └── Phase 3 (Excel Generator)
              ├── Phase 4 (Unit Tests)
              └── Phase 5 (Lambda Handler)
                    └── Phase 6 (Lambda Dependency Packaging)
                          └── Phase 7 (Terraform: S3)
                                └── Phase 8 (Terraform: IAM)
                                      └── Phase 9 (Terraform: Lambda)
                                            └── Phase 10 (Terraform: EventBridge)
                                                  └── Phase 11 (Terraform: Outputs)
                                                        └── Phase 12 (Documentation)
                                                              └── Phase 13 (Validation)
```

Each phase depends on all preceding phases being complete. Phases 4 (Unit Tests) and
5 (Lambda Handler) both depend on Phases 2 and 3, and can be developed in parallel
once Phase 3 is verified.

---

## Notes

- All verification checkpoints must pass before advancing to the next phase.
- Phases 4 and 5 share a common dependency on Phases 2–3 and may be worked in
  parallel, but Phase 6 requires both to be complete.
- Terraform phases (7–11) require `lambda.zip` to exist (produced in Phase 6) before
  `terraform plan` can succeed.
- The `scripts/package_lambda.sh` packaging script targets `manylinux2014_x86_64` for
  Lambda compatibility; do not omit the `--platform` flag when installing dependencies.
- No AWS credentials are required until `terraform apply` in Phase 13 validation;
  all earlier phases are locally verifiable.
- Dummy data in `data_provider.py` is intentionally hardcoded per REQ-3.4; replace
  `get_report_data()` with a real integration without touching any other module.
