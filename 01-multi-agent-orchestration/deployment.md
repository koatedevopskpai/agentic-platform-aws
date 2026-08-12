# Scenario 01 — Deployment Guide

## Architecture Overview (Deployed)

```
                                    ┌─────────────────────────────┐
                                    │   Route53 → CloudFront       │
                                    │   (custom domain)            │
                                    └──────────┬──────────────────┘
                                               │
                                    ┌──────────▼──────────────────┐
                                    │   API Gateway (REST)         │
                                    │   /analyze POST              │
                                    └──────────┬──────────────────┘
                                               │
                                    ┌──────────▼──────────────────┐
                                    │   NLB (internal)             │
                                    └──────────┬──────────────────┘
                                               │
┌─────────────────────────────┐    ┌──────────▼──────────────────┐
│   DynamoDB Sessions Table   │◄───│   ECS Fargate (Orchestrator) │
│   (on-demand, TTL 1h)       │    │   FastAPI + LangGraph       │
└─────────────────────────────┘    └──────────┬──────────────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
         ┌──────────▼──────────┐  ┌──────────▼──────────┐  ┌──────────▼──────────┐
         │  Lambda: search_news │  │ Lambda: competitor   │  │  Lambda: social      │
         │  (MCP tool executor) │  │ (MCP tool executor)  │  │  (MCP tool executor) │
         └─────────────────────┘  └──────────────────────┘  └─────────────────────┘
                    │                         │                         │
                    └─────────────────────────┼─────────────────────────┘
                                              │
                                    ┌─────────▼──────────┐
                                    │  S3 Artifact Store  │
                                    │  (results, traces)  │
                                    └────────────────────┘
                                    ┌─────────────────────┐
                                    │  CloudWatch Logs     │
                                    │  + Custom Metrics    │
                                    └─────────────────────┘
```

## Prerequisites

- AWS CLI configured with appropriate profile
- Terraform v1.5+
- Docker (for local Lambda testing)
- AWS account with Bedrock access (us-east-1)

---

## Method 1: Terraform (Primary)

```hcl
# modules/ecs-agent/main.tf
resource "aws_ecs_cluster" "this" {
  name = var.cluster_name
}

resource "aws_ecs_task_definition" "this" {
  family                   = var.task_family
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name      = "orchestrator"
      image     = var.container_image
      essential = true
      portMappings = [
        { containerPort = 8000, protocol = "tcp" }
      ]
      environment = [
        { name = "AGENTICOPS_ANTHROPIC_API_KEY", valueFrom = "${aws_secretsmanager_secret.anthropic.arn}" },
        { name = "SESSION_TABLE", value = var.session_table_name },
        { name = "ARTIFACT_BUCKET", value = var.artifact_bucket_name },
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.this.name
          "awslogs-region"        = data.aws_region.current.name
          "awslogs-stream-prefix" = "orchestrator"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "this" {
  name            = var.service_name
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.this.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = var.private_subnet_ids
    security_groups = [aws_security_group.this.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.this.arn
    container_name   = "orchestrator"
    container_port   = 8000
  }
}
```

### Deploy Commands

| Step | Terraform | AWS CLI | Console |
|------|-----------|---------|---------|
| 1. Create ECS cluster | `terraform apply -target=aws_ecs_cluster.this` | `aws ecs create-cluster --cluster-name AGENTICOPS-orchestrator` | ECS > Clusters > Create Cluster (Networking only) |
| 2. Create task definition | `terraform apply -target=aws_ecs_task_definition.this` | `aws ecs register-task-definition --cli-input-json file://task-def.json` | ECS > Task Definitions > Create (Fargate, 2vCPU, 4GB) |
| 3. Create DynamoDB table | `terraform apply -target=aws_dynamodb_table.sessions` | `aws dynamodb create-table --table-name AGENTICOPS-sessions-01 --attribute-definitions AttributeName=session_id,AttributeType=S --key-schema AttributeName=session_id,KeyType=HASH --billing-mode PAY_PER_REQUEST` | DynamoDB > Create Table ("AGENTICOPS-sessions-01", partition key: session_id) |
| 4. Create S3 bucket | `terraform apply -target=aws_s3_bucket.artifacts` | `aws s3 mb s3://AGENTICOPS-artifacts-01` | S3 > Create Bucket ("AGENTICOPS-artifacts-01") |
| 5. Create Lambda functions | `terraform apply -target=aws_lambda_function.search_news` | `aws lambda create-function --function-name AGENTICOPS-search-news --runtime python3.12 --role arn:aws:iam::xxx --handler main.handler --zip-file fileb://function.zip` | Lambda > Create Function ("AGENTICOPS-search-news") |
| 6. Create API Gateway | `terraform apply` | `aws apigateway create-rest-api --name AGENTICOPS-agent-api` | API Gateway > Create API > REST |
| 7. Create ECS service | `terraform apply` | `aws ecs create-service --cluster AGENTICOPS-orchestrator --service-name orchestrator-svc --task-definition AGENTICOPS-orchestrator:1 --desired-count 2 --launch-type FARGATE` | ECS > Clusters > AGENTICOPS-orchestrator > Services > Create |
| 8. Deploy container | `terraform apply` | `aws ecs update-service --cluster AGENTICOPS-orchestrator --service orchestrator-svc --force-new-deployment` | ECS > Clusters > Services > Update > Force new deployment |

## Environment Variables

| Variable | Source | Description |
|----------|--------|-------------|
| `AGENTICOPS_ANTHROPIC_API_KEY` | Secrets Manager `AGENTICOPS/anthropic/api-key` | Anthropic API key |
| `AGENTICOPS_OPENAI_API_KEY` | Secrets Manager `AGENTICOPS/openai/api-key` | OpenAI API key |
| `SESSION_TABLE` | DynamoDB table name | Session store |
| `ARTIFACT_BUCKET` | S3 bucket name | Artifact storage |
| `AGENTICOPS_LOG_LEVEL` | Config | Logging verbosity |

## Verification

```bash
# Test the deployed endpoint
curl -X POST https://api.AGENTICOPS.ai/analyze \
  -H "Content-Type: application/json" \
  -H "X-Client-Id: demo" \
  -d '{"query": "Analyze Nike brand sentiment"}'

# Check logs
aws logs tail /ecs/AGENTICOPS-orchestrator --follow

# Check metrics
aws cloudwatch get-metric-statistics \
  --namespace AgenticOps \
  --metric-name AgentLatency \
  --statistics Average p95 \
  --period 300 \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)
```

## Rollback

```bash
# Terraform
terraform plan -destroy -out=destroy.tfplan

# Manual
aws ecs update-service --cluster AGENTICOPS-orchestrator \
  --service orchestrator-svc \
  --task-definition AGENTICOPS-orchestrator:<previous-version>
```
