resource "aws_cloudwatch_log_group" "this" {
  for_each = var.log_group_names

  name              = each.value
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_arn

  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_cloudwatch_dashboard" "ai_platform" {
  dashboard_name = var.dashboard_name

  dashboard_body = jsonencode({
    widgets = concat(
      [
        {
          type = "text"
          x    = 0
          y    = 0
          width = 24
          height = 1
          properties = {
            markdown = "# AgenticOps - ${var.environment} AI Platform Dashboard"
          }
        },
        {
          type = "metric"
          x    = 0
          y    = 1
          width = 8
          height = 6
          properties = {
            metrics = [
              ["AgenticOps", "AgentLatency", { stat = "p95", label = "p95 Latency" }],
              ["AgenticOps", "AgentLatency", { stat = "Average", label = "Avg Latency" }],
            ]
            period = 300
            stat   = "Average"
            region = data.aws_region.current.name
            title  = "Agent Latency"
          }
        },
        {
          type = "metric"
          x    = 8
          y    = 1
          width = 8
          height = 6
          properties = {
            metrics = [
              ["AgenticOps", "TokenUsage", { stat = "Sum", label = "Total Tokens" }],
              ["AgenticOps", "TokenUsage", { stat = "Sum", label = "Input Tokens", period = 300 }],
            ]
            period = 300
            stat   = "Sum"
            region = data.aws_region.current.name
            title  = "Token Usage"
          }
        },
        {
          type = "metric"
          x    = 16
          y    = 1
          width = 8
          height = 6
          properties = {
            metrics = [
              ["AgenticOps", "Cost", { stat = "Sum", label = "API Cost" }],
            ]
            period = 3600
            stat   = "Sum"
            region = data.aws_region.current.name
            title  = "LLM API Cost ($)"
          }
        },
        {
          type = "metric"
          x    = 0
          y    = 7
          width = 8
          height = 6
          properties = {
            metrics = [
              ["AgenticOps", "EvalScore", { stat = "Average", label = "Avg Eval Score" }],
            ]
            period = 3600
            stat   = "Average"
            region = data.aws_region.current.name
            title  = "Eval Quality Score"
          }
        },
        {
          type = "metric"
          x    = 8
          y    = 7
          width = 8
          height = 6
          properties = {
            metrics = [
              ["AgenticOps", "AgentCount", { stat = "Sum", label = "Agent Requests" }],
            ]
            period = 300
            stat   = "Sum"
            region = data.aws_region.current.name
            title  = "Request Volume"
          }
        },
        {
          type = "metric"
          x    = 16
          y    = 7
          width = 8
          height = 6
          properties = {
            metrics = [
              ["AgenticOps", "GuardrailBlocks", { stat = "Sum", label = "Guardrail Blocks" }],
            ]
            period = 3600
            stat   = "Sum"
            region = data.aws_region.current.name
            title  = "Guardrail Blocks"
          }
        },
      ],
      var.additional_widgets
    )
  })
}

resource "aws_cloudwatch_metric_alarm" "high_latency" {
  alarm_name          = "${var.environment}-high-agent-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "AgentLatency"
  namespace           = "AgenticOps"
  period              = 300
  statistic           = "p95"
  threshold           = var.high_latency_threshold_ms
  alarm_description   = "Agent latency exceeds ${var.high_latency_threshold_ms}ms p95"
  alarm_actions       = var.alarm_sns_topics

  tags = {
    Environment = var.environment
  }
}

resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  alarm_name          = "${var.environment}-high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ErrorRate"
  namespace           = "AgenticOps"
  period              = 300
  statistic           = "Average"
  threshold           = var.high_error_rate_threshold
  alarm_description   = "Error rate exceeds ${var.high_error_rate_threshold * 100}%"
  alarm_actions       = var.alarm_sns_topics

  tags = {
    Environment = var.environment
  }
}

resource "aws_cloudwatch_metric_alarm" "cost_anomaly" {
  alarm_name          = "${var.environment}-cost-anomaly"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Cost"
  namespace           = "AgenticOps"
  period              = 86400
  statistic           = "Sum"
  threshold           = var.daily_cost_threshold
  alarm_description   = "Daily LLM cost exceeds $${var.daily_cost_threshold}"
  alarm_actions       = var.alarm_sns_topics

  tags = {
    Environment = var.environment
  }
}

resource "aws_cloudwatch_metric_alarm" "eval_score_drop" {
  alarm_name          = "${var.environment}-eval-score-drop"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 3
  metric_name         = "EvalScore"
  namespace           = "AgenticOps"
  period              = 3600
  statistic           = "Average"
  threshold           = var.eval_score_threshold
  alarm_description   = "Average eval score below ${var.eval_score_threshold}"
  alarm_actions       = var.alarm_sns_topics

  tags = {
    Environment = var.environment
  }
}

data "aws_region" "current" {}
