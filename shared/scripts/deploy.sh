#!/bin/bash
set -euo pipefail

# AgenticOps Deployment Script
# Usage: ./deploy.sh <environment> <scenario>

ENVIRONMENT="${1:-dev}"
SCENARIO="${2:-01}"

echo "=== AgenticOps Deployment ==="
echo "Environment: ${ENVIRONMENT}"
echo "Scenario: ${SCENARIO}"
echo ""

case "${SCENARIO}" in
  01)
    echo "Deploying Multi-Agent Orchestrator to ${ENVIRONMENT}..."
    
    # Build and push container
    cd 01-multi-agent-orchestration
    docker build -t AGENTICOPS-orchestrator:latest .
    
    # Tag for ECR
    aws ecr get-login-password --region us-east-1 | \
      docker login --username AWS --password-stdin \
      "${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com"
    
    docker tag AGENTICOPS-orchestrator:latest \
      "${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/AGENTICOPS-orchestrator:latest"
    docker push "${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/AGENTICOPS-orchestrator:latest"
    
    # Deploy ECS service
    aws ecs update-service \
      --cluster "AGENTICOPS-orchestrator-${ENVIRONMENT}" \
      --service "orchestrator-svc-${ENVIRONMENT}" \
      --force-new-deployment \
      --region us-east-1
    
    echo "Orchestrator deployed successfully"
    ;;
    
  02)
    echo "Deploying Eval Platform to ${ENVIRONMENT}..."
    
    # Deploy Lambda functions
    cd 02-llm-eval-platform
    
    # Package eval runner
    pip install -e . -t build/
    cd build && zip -r ../eval-runner.zip . && cd ..
    
    aws lambda update-function-code \
      --function-name "AGENTICOPS-eval-runner-${ENVIRONMENT}" \
      --zip-file fileb://eval-runner.zip \
      --region us-east-1
    
    # Sync prompts
    aws s3 sync prompts/ \
      "s3://AGENTICOPS-eval-datasets-${ENVIRONMENT}/prompts/" \
      --delete \
      --region us-east-1
    
    echo "Eval platform deployed successfully"
    ;;
    
  *)
    echo "Unknown scenario: ${SCENARIO}"
    echo "Usage: ./deploy.sh <environment> <scenario>"
    exit 1
    ;;
esac

echo ""
echo "=== Deployment Complete ==="
