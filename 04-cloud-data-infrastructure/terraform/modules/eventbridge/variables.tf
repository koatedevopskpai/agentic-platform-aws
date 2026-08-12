variable "event_bus_name" {
  description = "Name of the event bus"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "scheduled_rules" {
  description = "Map of scheduled rules"
  type = map(object({
    description        = string
    schedule_expression = string
    target_arn         = string
    input_payload      = optional(map(any))
  }))
  default = {}
}

variable "event_pattern_rules" {
  description = "Map of event pattern rules"
  type = map(object({
    description   = string
    event_pattern = map(any)
    target_arn    = string
    input_payload = optional(map(any))
  }))
  default = {}
}
