resource "aws_lambda_function" "this" {
  function_name = var.function_name
  role          = aws_iam_role.this.arn
  runtime       = var.runtime
  handler       = var.handler
  timeout       = var.timeout
  memory_size   = var.memory_size
  publish       = var.publish_new_version

  filename         = var.filename != null ? var.filename : null
  s3_bucket        = var.s3_bucket
  s3_key           = var.s3_key
  image_uri        = var.image_uri
  package_type     = var.image_uri != null ? "Image" : "Zip"
  source_code_hash = var.source_code_hash

  dynamic "environment" {
    for_each = length(var.environment_variables) > 0 ? [1] : []
    content {
      variables = var.environment_variables
    }
  }

  dynamic "vpc_config" {
    for_each = var.vpc_subnet_ids != null ? [1] : []
    content {
      subnet_ids         = var.vpc_subnet_ids
      security_group_ids = var.vpc_security_group_ids
    }
  }

  reserved_concurrent_executions = var.reserved_concurrency

  tracing_config {
    mode = var.xray_tracing_enabled ? "Active" : "PassThrough"
  }

  tags = {
    Name        = var.function_name
    Environment = var.environment
    ManagedBy   = "terraform"
    CostCenter  = "ai-platform"
  }
}

resource "aws_iam_role" "this" {
  name = "${var.function_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "basic" {
  name = "${var.function_name}-basic-policy"
  role = aws_iam_role.this.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat(
      [
        {
          Effect = "Allow"
          Action = [
            "logs:CreateLogGroup",
            "logs:CreateLogStream",
            "logs:PutLogEvents",
          ]
          Resource = "*"
        },
      ],
      var.extra_iam_policy_statements
    )
  })
}

resource "aws_cloudwatch_log_group" "this" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = var.log_retention_days

  tags = {
    Environment = var.environment
  }
}

resource "aws_lambda_permission" "invoke" {
  count         = length(var.allowed_triggers)
  statement_id  = "AllowInvokeFrom${count.index}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this.function_name
  principal     = var.allowed_triggers[count.index].principal
  source_arn    = var.allowed_triggers[count.index].source_arn
}
