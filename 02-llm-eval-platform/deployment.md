# Scenario 02 — Deployment Guide

## Architecture Overview (Deployed)

```
                                    ┌─────────────────────────────┐
                                    │   EventBridge Schedule       │
                                    │   (daily eval run trigger)   │
                                    └──────────┬──────────────────┘
                                               │
                                    ┌──────────▼──────────────────┐
                                    │   Step Functions             │
                                    │   (Eval Pipeline)            │
                                    └──────────┬──────────────────┘
                                               │
                    ┌───────────────────────────┼───────────────────────────┐
                    │                           │                           │
         ┌──────────▼──────────┐    ┌──────────▼──────────┐    ┌──────────▼──────────┐
         │  Lambda: Eval       │    │  Lambda: Guardrails │    │  Lambda: Dashboard   │
         │  Runner             │    │  Engine             │    │  Generator           │
         │  (16GB, 5min)       │    │  (1GB, 30s)         │    │  (1GB, 1min)         │
         └──────────┬──────────┘    └──────────┬──────────┘    └──────────┬──────────┘
                    │                          │                          │
                    └──────────────────────────┼──────────────────────────┘
                                               │
                                    ┌──────────▼──────────┐
                                    │  DynamoDB            │
                                    │  (Eval Results Table)│
                                    │  (on-demand, TTL 90d)│
                                    └─────────────────────┘
                                    ┌─────────────────────┐
                                    │  S3                  │
                                    │  (Golden Dataset +   │
                                    │   Prompt Registry)   │
                                    └─────────────────────┘
                                    ┌─────────────────────┐
                                    │  CloudWatch          │
                                    │  (Logs + Dashboard)  │
                                    └─────────────────────┘
```

## Prerequisites

- AWS CLI configured with appropriate profile
- Terraform v1.5+
- LangSmith API key (for tracing)
- AWS Bedrock access (us-east-1)

---

## Method 1: Terraform (Primary)

```hcl
# modules/lambda-eval/main.tf
resource "aws_lambda_function" "eval_runner" {
  function_name = var.function_name
  runtime       = "python3.12"
  handler       = "handler.lambda_handler"
  role          = aws_iam_role.eval_role.arn
  timeout       = 300
  memory_size   = 16384

  environment {
    variables = {
      AGENTICOPS_ANTHROPIC_API_KEY = var.anthropic_api_key_arn
      AGENTICOPS_OPENAI_API_KEY    = var.openai_api_key_arn
      AGENTICOPS_RESULTS_TABLE     = var.results_table_name
      AGENTICOPS_DATASET_BUCKET    = var.dataset_bucket_name
      AGENTICOPS_LOG_LEVEL         = "INFO"
    }
  }
}

resource "aws_cloudwatch_event_rule" "daily_eval" {
  name                = "daily-eval-run"
  schedule_expression = "cron(0 6 * * ? *)"
}

resource "aws_cloudwatch_event_target" "daily_eval" {
  rule  = aws_cloudwatch_event_rule.daily_eval.name
  arn   = aws_lambda_function.eval_runner.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.eval_runner.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_eval.arn
}
```

### Deploy Commands

| Step | Terraform | AWS CLI | Console |
|------|-----------|---------|---------|
| 1. Create DynamoDB results table | `terraform apply -target=aws_dynamodb_table.results` | `aws dynamodb create-table --table-name AGENTICOPS-eval-results --attribute-definitions AttributeName=eval_id,AttributeType=S --key-schema AttributeName=eval_id,KeyType=HASH --billing-mode PAY_PER_REQUEST` | DynamoDB > Create Table ("AGENTICOPS-eval-results", partition key: eval_id) |
| 2. Create S3 bucket for datasets | `terraform apply -target=aws_s3_bucket.datasets` | `aws s3 mb s3://AGENTICOPS-eval-datasets` | S3 > Create Bucket ("AGENTICOPS-eval-datasets") |
| 3. Upload golden dataset | `terraform apply -target=aws_s3_object.golden_dataset` | `aws s3 cp prompts/golden_v1/ s3://AGENTICOPS-eval-datasets/golden_v1/ --recursive` | S3 > Upload > Select files |
| 4. Create eval runner Lambda | `terraform apply -target=aws_lambda_function.eval_runner` | `aws lambda create-function --function-name AGENTICOPS-eval-runner --runtime python3.12 --role arn:aws:iam::xxx --handler handler.lambda_handler --zip-file fileb://deployment.zip --timeout 300 --memory-size 16384` | Lambda > Create Function ("AGENTICOPS-eval-runner", Python 3.12, 16GB, 5min timeout) |
| 5. Create guardrail Lambda | `terraform apply -target=aws_lambda_function.guardrails` | `aws lambda create-function --function-name AGENTICOPS-guardrails --runtime python3.12 --role arn:aws:iam::xxx --handler guard_handler.lambda_handler --zip-file fileb://guard_deploy.zip --timeout 30 --memory-size 1024` | Lambda > Create Function ("AGENTICOPS-guardrails") |
| 6. Schedule daily eval run | `terraform apply` | `aws events put-rule --name daily-eval-run --schedule-expression "cron(0 6 * * ? *)"` | EventBridge > Rules > Create ("daily-eval-run", cron(0 6 * * ? *)) |
| 7. Upload prompt registry | Manual step | `aws s3 cp prompts/registry/ s3://AGENTICOPS-eval-datasets/registry/ --recursive` | S3 > Upload prompt YAML files |

## Environment Variables

| Variable | Source | Description |
|----------|--------|-------------|
| `AGENTICOPS_ANTHROPIC_API_KEY` | Secrets Manager | Anthropic API key for judge LLM |
| `AGENTICOPS_OPENAI_API_KEY` | Secrets Manager | OpenAI API key (fallback) |
| `AGENTICOPS_RESULTS_TABLE` | DynamoDB | Eval results table |
| `AGENTICOPS_DATASET_BUCKET` | S3 | Golden dataset location |
| `LANGCHAIN_API_KEY` | Secrets Manager | LangSmith API key |
| `AGENTICOPS_LOG_LEVEL` | Config | Logging verbosity |

## Verification

```bash
# Run a manual eval
aws lambda invoke --function-name AGENTICOPS-eval-runner \
  --payload '{"dataset": "golden_v1", "model": "claude-sonnet-4"}' \
  response.json

# Check results
aws dynamodb scan --table-name AGENTICOPS-eval-results --max-items 10

# View CloudWatch dashboard
aws cloudwatch get-dashboard --dashboard-name AGENTICOPS-eval-dashboard

# Run guardrails
aws lambda invoke --function-name AGENTICOPS-guardrails \
  --payload '{"text": "Test email: user@example.com"}' \
  guard_response.json
```

## Rollback

```bash
# Rollback to previous dataset version
aws s3 sync s3://AGENTICOPS-eval-datasets/golden_v0/ s3://AGENTICOPS-eval-datasets/golden_v1/

# Rollback Lambda
aws lambda update-function-code \
  --function-name AGENTICOPS-eval-runner \
  --s3-bucket AGENTICOPS-deployments \
  --s3-key eval-runner-v0.9.zip

# Rollback prompt registry
aws s3 sync s3://AGENTICOPS-eval-datasets/registry_previous/ s3://AGENTICOPS-eval-datasets/registry/
```
