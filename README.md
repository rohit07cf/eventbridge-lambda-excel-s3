# eventbridge-lambda-excel-s3

A scheduled cost-reporting workflow on AWS. Every five minutes, Amazon EventBridge
invokes a Python Lambda function that builds an Excel workbook in memory and uploads
it to a private S3 bucket. All infrastructure is managed with Terraform.

## Architecture

```
┌────────────────────┐  rate(5 minutes)  ┌──────────────────────────┐
│ Amazon EventBridge │ ────────────────▶ │ AWS Lambda (python3.12)  │
└────────────────────┘                   │  lambda_function.py      │
                                         │   ├─ data_provider.py    │  get_report_data() → list[dict]
                                         │   └─ excel_generator.py  │  generate_excel(rows) → BytesIO
                                         └────────────┬─────────────┘
                                                      │ s3:PutObject
                                   ┌──────────────────┴─────────────────┐
                                   ▼                                    ▼
                  S3: processed/cost-report-YYYY-MM-DD-HHMMSS.xlsx   CloudWatch Logs
```

See [.kiro/specs/eventbridge-lambda-excel-s3/design.md](.kiro/specs/eventbridge-lambda-excel-s3/design.md)
for the full design.

## Repository Structure

```
eventbridge-lambda-excel-s3/
├── .kiro/specs/eventbridge-lambda-excel-s3/   ← requirements, design, tasks
├── src/
│   ├── lambda_function.py      ← Lambda handler (orchestrator)
│   ├── data_provider.py        ← Report data layer (dummy implementation)
│   ├── excel_generator.py      ← Excel workbook generation
│   └── requirements.txt        ← Lambda runtime dependencies (openpyxl)
├── tests/
│   └── test_excel_generator.py ← Unit tests for Excel generation
├── terraform/
│   ├── providers.tf            ← AWS provider + Terraform version constraint
│   ├── variables.tf            ← Input variables
│   ├── main.tf                 ← Locals, data sources
│   ├── s3.tf                   ← S3 bucket, encryption, public access block
│   ├── iam.tf                  ← Lambda execution role + least-privilege policy
│   ├── lambda.tf               ← Lambda function
│   ├── eventbridge.tf          ← Schedule rule, target, invoke permission
│   └── outputs.tf              ← Outputs
├── scripts/
│   └── package_lambda.sh       ← Builds lambda.zip (source + openpyxl)
├── requirements-dev.txt        ← Local dev/test dependencies
└── README.md
```

## Prerequisites

| Tool      | Minimum version |
|-----------|-----------------|
| Python    | 3.12            |
| pip       | any recent      |
| Terraform | 1.5             |
| AWS CLI   | v2              |
| bash, zip | any             |

You also need AWS credentials that can create the resources listed under
[Configuration reference](#configuration-reference).

## Local development

### Install Python dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

### Run unit tests

```bash
pytest tests/ -v
```

The tests cover the Excel generator only and make no AWS calls.

## Deployment

### 1. Package the Lambda

```bash
bash scripts/package_lambda.sh
```

This writes `lambda.zip` to the repository root. It contains the three source files
and `openpyxl`, which the Lambda runtime does not provide. `boto3` comes with the runtime,
so the ZIP leaves it out. **Terraform reads this file, so run the script before
`terraform plan`. Run it again after every source change.**

### 2. Initialise Terraform

```bash
cd terraform
terraform init
```

### 3. Check formatting and validate

```bash
terraform fmt -recursive
terraform validate
```

### 4. Plan

```bash
terraform plan -var="environment=dev" -var="project_name=cost-report"
```

### 5. Apply

```bash
terraform apply -var="environment=dev" -var="project_name=cost-report"
```

S3 bucket names are global, so the bucket name `${project_name}-${environment}-reports`
must be unique across all AWS accounts. If `apply` fails because the bucket name is
taken, change `project_name`.

## Operations

Get the resource names from Terraform:

```bash
terraform output
```

### Manually invoke the Lambda

```bash
aws lambda invoke \
  --function-name "$(terraform output -raw lambda_function_name)" \
  response.json
cat response.json
```

A successful response looks like this:

```json
{"status": "success", "bucket": "cost-report-dev-reports", "key": "processed/cost-report-2026-09-26-120000.xlsx", "rows_processed": 6}
```

### Verify S3 output

```bash
aws s3 ls "s3://$(terraform output -raw s3_bucket_name)/processed/"
```

### Check CloudWatch Logs

```bash
aws logs tail "/aws/lambda/$(terraform output -raw lambda_function_name)" --follow
```

Each run logs these lines in order: `Lambda execution started`, `Report data generation started`,
`Excel generation started`, `S3 upload started`, `S3 upload completed`,
`Lambda execution completed successfully`. If a run fails, the log shows
`Unhandled exception during execution` with a full traceback.

### Verify EventBridge execution

In the AWS console, go to **Amazon EventBridge → Rules** and open the
`<project_name>-<environment>-schedule` rule. The **Monitoring** tab shows
`Invocations` and `FailedInvocations`. You can also query the CloudWatch metrics
from the CLI:

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Events \
  --metric-name Invocations \
  --dimensions Name=RuleName,Value="$(terraform output -raw eventbridge_rule_name)" \
  --start-time "$(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --period 300 --statistics Sum
```

On Linux, use `date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ` for `--start-time`.
`FailedInvocations` should be 0. Check the Lambda's own `Errors` metric in the
`AWS/Lambda` namespace as well.

### Destroy

```bash
terraform destroy -var="environment=dev" -var="project_name=cost-report"
```

Terraform will not delete a bucket that still contains objects. Empty it first:
`aws s3 rm "s3://$(terraform output -raw s3_bucket_name)" --recursive`.

## Configuration reference

### Terraform variables

| Variable              | Type   | Default             | Description                                 |
|-----------------------|--------|---------------------|---------------------------------------------|
| `aws_region`          | string | `"us-east-1"`       | AWS region for all resources                |
| `environment`         | string | *(required)*        | Deployment environment (e.g. `dev`, `prod`) |
| `project_name`        | string | *(required)*        | Project identifier used in resource names   |
| `schedule_expression` | string | `"rate(5 minutes)"` | EventBridge schedule expression             |
| `lambda_memory_size`  | number | `256`               | Lambda memory in MB                         |
| `lambda_timeout`      | number | `30`                | Lambda timeout in seconds                   |

### Terraform outputs

| Output                  | Description                                            |
|-------------------------|--------------------------------------------------------|
| `s3_bucket_name`        | Name of the S3 bucket that receives Excel cost reports |
| `lambda_function_name`  | Name of the Lambda function that generates reports     |
| `eventbridge_rule_name` | Name of the EventBridge scheduled rule                 |

### Lambda environment variables

| Variable        | Set by                                   | Description                    |
|-----------------|------------------------------------------|--------------------------------|
| `OUTPUT_BUCKET` | Terraform (`aws_lambda_function` block)  | S3 bucket for workbook uploads |

### Resources created

| Resource                                              | Name                                   |
|-------------------------------------------------------|----------------------------------------|
| `aws_s3_bucket` (+ public access block, SSE-S3)       | `<prefix>-reports`                     |
| `aws_iam_role` + inline `aws_iam_role_policy`         | `<prefix>-lambda-role` / `-lambda-policy` |
| `aws_lambda_function`                                 | `<prefix>-cost-report`                 |
| `aws_cloudwatch_event_rule` + target                  | `<prefix>-schedule`                    |
| `aws_lambda_permission`                               | `AllowEventBridgeInvoke`               |

`<prefix>` is `${project_name}-${environment}`. The IAM policy grants only
`s3:PutObject` on `processed/*` of the report bucket, plus CloudWatch Logs write
access for this function's log group.

## Replacing the dummy data

`data_provider.get_report_data()` returns six hard-coded rows. To use a real data
source such as Flexera, Apptio, or an S3 input, replace that function's body. It must
return rows in the same schema, which is documented in the module docstring. No other
module needs to change.
