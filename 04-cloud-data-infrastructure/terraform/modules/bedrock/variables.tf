variable "environment" {
  description = "Environment name"
  type        = string
}

variable "provisioned_models" {
  description = "Map of provisioned models"
  type = map(object({
    model_id             = string
    model_units          = number
    commitment_duration  = string
  }))
  default = {}
}

variable "allowed_models" {
  description = "List of allowed model IDs for invocation"
  type        = list(string)
  default = [
    "anthropic.claude-sonnet-4-v1",
    "anthropic.claude-haiku-3-5-v1:0",
    "meta.llama3-1-405b-instruct-v1:0",
    "amazon.titan-embed-text-v2:0",
  ]
}

variable "create_guardrails" {
  description = "Create Bedrock guardrails"
  type        = bool
  default     = true
}

variable "enable_model_logging" {
  description = "Enable Bedrock model invocation logging"
  type        = bool
  default     = true
}

variable "logging_bucket_name" {
  description = "S3 bucket name for Bedrock invocation logs"
  type        = string
  default     = null
}
