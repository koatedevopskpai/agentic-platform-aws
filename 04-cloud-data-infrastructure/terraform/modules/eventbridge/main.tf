resource "aws_cloudwatch_event_bus" "this" {
  name = var.event_bus_name

  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_cloudwatch_event_rule" "scheduled" {
  for_each = var.scheduled_rules

  name                = each.key
  description         = each.value.description
  schedule_expression = each.value.schedule_expression
  event_bus_name      = aws_cloudwatch_event_bus.this.name

  tags = {
    Environment = var.environment
  }
}

resource "aws_cloudwatch_event_rule" "event_pattern" {
  for_each = var.event_pattern_rules

  name           = each.key
  description    = each.value.description
  event_pattern  = jsonencode(each.value.event_pattern)
  event_bus_name = aws_cloudwatch_event_bus.this.name

  tags = {
    Environment = var.environment
  }
}

resource "aws_cloudwatch_event_target" "scheduled" {
  for_each = var.scheduled_rules

  rule           = aws_cloudwatch_event_rule.scheduled[each.key].name
  event_bus_name = aws_cloudwatch_event_bus.this.name
  arn            = each.value.target_arn

  input = each.value.input_payload != null ? jsonencode(each.value.input_payload) : null
}

resource "aws_cloudwatch_event_target" "event_pattern" {
  for_each = var.event_pattern_rules

  rule           = aws_cloudwatch_event_rule.event_pattern[each.key].name
  event_bus_name = aws_cloudwatch_event_bus.this.name
  arn            = each.value.target_arn

  input = each.value.input_payload != null ? jsonencode(each.value.input_payload) : null
}

# Agent lifecycle events topic
resource "aws_sns_topic" "agent_events" {
  name = "${var.environment}-agent-events"

  tags = {
    Environment = var.environment
  }
}

resource "aws_cloudwatch_event_rule" "agent_events" {
  name        = "${var.environment}-capture-agent-events"
  description = "Capture all agent lifecycle events"

  event_pattern = jsonencode({
    source      = ["AGENTICOPS.agent"]
    detail-type = ["AgentStarted", "AgentCompleted", "AgentFailed", "ToolCalled", "ToolResult"]
  })

  tags = {
    Environment = var.environment
  }
}

resource "aws_cloudwatch_event_target" "agent_events_sns" {
  rule      = aws_cloudwatch_event_rule.agent_events.name
  arn       = aws_sns_topic.agent_events.arn
}
