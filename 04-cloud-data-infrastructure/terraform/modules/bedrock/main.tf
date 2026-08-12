data "aws_region" "current" {}

# Enable Bedrock in the region
resource "aws_bedrock_provisioned_model_throughput" "this" {
  for_each = var.provisioned_models

  model_units      = each.value.model_units
  model_id         = each.value.model_id
  commitment_duration = each.value.commitment_duration

  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# IAM policy for Bedrock invocation
data "aws_iam_policy_document" "bedrock_invoke" {
  statement {
    effect = "Allow"
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream",
    ]
    resources = [
      for model in var.allowed_models :
      "arn:aws:bedrock:${data.aws_region.current.name}:*:model/${model}"
    ]
  }
}

# Guardrails for Bedrock
resource "aws_bedrock_guardrail" "content_policy" {
  count                      = var.create_guardrails ? 1 : 0
  name                       = "${var.environment}-content-guardrail"
  description                = "Content safety guardrail for AgenticOps agent outputs"
  blocked_input_messaging    = "Input blocked by content safety policy"
  blocked_outputs_messaging  = "Output blocked by content safety policy"

  content_policy_config {
    filters_config {
      input_strength  = "HIGH"
      output_strength = "HIGH"
      type            = "HATE"
    }
    filters_config {
      input_strength  = "HIGH"
      output_strength = "HIGH"
      type            = "INSULTS"
    }
    filters_config {
      input_strength  = "HIGH"
      output_strength = "HIGH"
      type            = "SEXUAL"
    }
    filters_config {
      input_strength  = "HIGH"
      output_strength = "HIGH"
      type            = "VIOLENCE"
    }
    filters_config {
      input_strength  = "HIGH"
      output_strength = "HIGH"
      type            = "MISCONDUCT"
    }
    filters_config {
      input_strength  = "MEDIUM"
      output_strength = "MEDIUM"
      type            = "PROMPT_ATTACK"
    }
  }

  sensitive_information_policy_config {
    pii_entities_config {
      action = "BLOCK"
      type   = "EMAIL"
    }
    pii_entities_config {
      action = "BLOCK"
      type   = "PHONE"
    }
    pii_entities_config {
      action = "BLOCK"
      type   = "US_SOCIAL_SECURITY_NUMBER"
    }
    regexes_config {
      action      = "BLOCK"
      description = "AWS Access Key"
      pattern     = "AKIA[0-9A-Z]{16}"
    }
  }

  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_bedrock_guardrail_version" "content_policy" {
  count          = var.create_guardrails ? 1 : 0
  guardrail_arn  = aws_bedrock_guardrail.content_policy[0].arn
  description    = "Auto-versioned deployment"
  skip_destroy   = false
}

# Bedrock model invocation logging
resource "aws_bedrock_model_invocation_logging_configuration" "this" {
  count = var.enable_model_logging ? 1 : 0

  logging_config {
    embedding_data_delivery_enabled = true
    image_data_delivery_enabled     = true
    text_data_delivery_enabled      = true

    s3_config {
      bucket_name       = var.logging_bucket_name
      key_prefix        = "bedrock-invocations/"
    }

    cloudwatch_config {
      log_group_name    = "/aws/bedrock/invocations"
      role_arn          = aws_iam_role.bedrock_logging[0].arn
      large_data_delivery_s3_config {
        bucket_name     = var.logging_bucket_name
        key_prefix      = "bedrock-large-data/"
      }
    }
  }
}

resource "aws_iam_role" "bedrock_logging" {
  count = var.enable_model_logging ? 1 : 0
  name  = "${var.environment}-bedrock-logging"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}
