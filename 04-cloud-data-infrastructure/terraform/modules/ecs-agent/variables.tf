variable "cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
}

variable "task_family" {
  description = "Family name for the task definition"
  type        = string
}

variable "service_name" {
  description = "Name of the ECS service"
  type        = string
}

variable "container_name" {
  description = "Name of the container"
  type        = string
  default     = "app"
}

variable "container_image" {
  description = "Container image URI"
  type        = string
}

variable "container_port" {
  description = "Container port"
  type        = number
  default     = 8000
}

variable "cpu" {
  description = "CPU units for Fargate task"
  type        = string
  default     = "1024"
}

variable "memory" {
  description = "Memory for Fargate task"
  type        = string
  default     = "2048"
}

variable "desired_count" {
  description = "Desired number of tasks"
  type        = number
  default     = 2
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs"
  type        = list(string)
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs"
  type        = list(string)
}

variable "internal_alb" {
  description = "Whether the ALB is internal"
  type        = bool
  default     = false
}

variable "certificate_arn" {
  description = "ARN of the ACM certificate"
  type        = string
  default     = ""
}

variable "session_table_name" {
  description = "Name of the DynamoDB session table"
  type        = string
}

variable "artifact_bucket_name" {
  description = "Name of the S3 artifact bucket"
  type        = string
}

variable "log_level" {
  description = "Logging level"
  type        = string
  default     = "INFO"
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 90
}

variable "secrets" {
  description = "List of secrets to inject"
  type = list(object({
    name = string
    arn  = string
  }))
  default = []
}

variable "secret_arns" {
  description = "ARNs of secrets for execution role"
  type        = list(string)
  default     = []
}

variable "kms_key_arns" {
  description = "ARNs of KMS keys for decryption"
  type        = list(string)
  default     = []
}

variable "bedrock_model_arns" {
  description = "ARNs of Bedrock models to allow access to"
  type        = list(string)
  default     = []
}

variable "extra_environment_variables" {
  description = "Additional environment variables"
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}

variable "enable_execute_command" {
  description = "Enable ECS Exec for debugging"
  type        = bool
  default     = false
}
