variable "environment" {
  description = "Environment name"
  type        = string
}

variable "dashboard_name" {
  description = "CloudWatch dashboard name"
  type        = string
  default     = "AGENTICOPS-ai-platform"
}

variable "log_group_names" {
  description = "Map of log group names to create"
  type        = map(string)
  default     = {}
}

variable "log_retention_days" {
  description = "Log retention in days"
  type        = number
  default     = 90
}

variable "kms_key_arn" {
  description = "KMS key ARN for log encryption"
  type        = string
  default     = null
}

variable "alarm_sns_topics" {
  description = "SNS topic ARNs for alarm notifications"
  type        = list(string)
  default     = []
}

variable "high_latency_threshold_ms" {
  description = "High latency alarm threshold in milliseconds"
  type        = number
  default     = 5000
}

variable "high_error_rate_threshold" {
  description = "High error rate alarm threshold (0.0-1.0)"
  type        = number
  default     = 0.05
}

variable "daily_cost_threshold" {
  description = "Daily cost alarm threshold in USD"
  type        = number
  default     = 500
}

variable "eval_score_threshold" {
  description = "Minimum eval score before alarm"
  type        = number
  default     = 0.7
}

variable "additional_widgets" {
  description = "Additional CloudWatch dashboard widgets"
  type        = list(any)
  default     = []
}
