terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "AGENTICOPS-terraform-state"
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "AGENTICOPS-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = "dev"
      ManagedBy   = "terraform"
      CostCenter  = "ai-platform-dev"
    }
  }
}

module "networking" {
  source = "../../modules/networking"

  vpc_cidr             = "10.0.0.0/16"
  vpc_name             = "AGENTICOPS-dev"
  environment          = "dev"
  availability_zones   = ["us-east-1a", "us-east-1b"]
  private_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnet_cidrs  = ["10.0.101.0/24", "10.0.102.0/24"]
  single_nat_gateway   = true
}

module "dynamodb_sessions" {
  source = "../../modules/dynamodb"

  table_name   = "AGENTICOPS-sessions-dev"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "session_id"
  environment  = "dev"

  attributes = [
    { name = "session_id", type = "S" },
  ]

  ttl_enabled      = true
  ttl_attribute_name = "ttl"
}

module "dynamodb_eval_results" {
  source = "../../modules/dynamodb"

  table_name   = "AGENTICOPS-eval-results-dev"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "eval_id"
  environment  = "dev"

  attributes = [
    { name = "eval_id", type = "S" },
  ]
}

module "s3_artifacts" {
  source = "../../modules/s3-artifact"

  bucket_name              = "AGENTICOPS-artifacts-dev"
  environment              = "dev"
  versioning_enabled       = true
  artifact_expiration_days = 30
}

module "observability" {
  source = "../../modules/observability"

  environment    = "dev"
  dashboard_name = "AGENTICOPS-dev-platform"

  log_group_names = {
    ecs_agents   = "/ecs/AGENTICOPS-dev-agents"
    eval_runners = "/aws/lambda/AGENTICOPS-eval-runner-dev"
    bedrock      = "/aws/bedrock/invocations"
  }
}

module "bedrock" {
  source = "../../modules/bedrock"

  environment          = "dev"
  create_guardrails    = true
  enable_model_logging = true
  logging_bucket_name  = module.s3_artifacts.bucket_name

  allowed_models = [
    "anthropic.claude-sonnet-4-v1",
    "anthropic.claude-haiku-3-5-v1:0",
    "meta.llama3-1-405b-instruct-v1:0",
  ]
}
