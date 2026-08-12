variable "function_name" {
  description = "Lambda function name"
  type        = string
}

variable "runtime" {
  description = "Lambda runtime"
  type        = string
  default     = "python3.12"
}

variable "handler" {
  description = "Lambda handler"
  type        = string
  default     = "handler.lambda_handler"
}

variable "timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 30
}

variable "memory_size" {
  description = "Lambda memory size in MB"
  type        = number
  default     = 1024
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "environment_variables" {
  description = "Environment variables"
  type        = map(string)
  default     = {}
}

variable "filename" {
  description = "Local path to the Lambda deployment package"
  type        = string
  default     = null
}

variable "s3_bucket" {
  description = "S3 bucket for Lambda deployment package"
  type        = string
  default     = null
}

variable "s3_key" {
  description = "S3 key for Lambda deployment package"
  type        = string
  default     = null
}

variable "image_uri" {
  description = "ECR image URI for container-based Lambda"
  type        = string
  default     = null
}

variable "source_code_hash" {
  description = "Base64-encoded SHA256 hash of the deployment package"
  type        = string
  default     = null
}

variable "publish_new_version" {
  description = "Publish a new Lambda version"
  type        = bool
  default     = false
}

variable "reserved_concurrency" {
  description = "Reserved concurrency for the Lambda"
  type        = number
  default     = -1
}

variable "vpc_subnet_ids" {
  description = "VPC subnet IDs"
  type        = list(string)
  default     = null
}

variable "vpc_security_group_ids" {
  description = "VPC security group IDs"
  type        = list(string)
  default     = null
}

variable "xray_tracing_enabled" {
  description = "Enable X-Ray tracing"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 90
}

variable "extra_iam_policy_statements" {
  description = "Additional IAM policy statements"
  type        = list(any)
  default     = []
}

variable "allowed_triggers" {
  description = "List of allowed trigger principals and source ARNs"
  type = list(object({
    principal = string
    source_arn = string
  }))
  default = []
}
