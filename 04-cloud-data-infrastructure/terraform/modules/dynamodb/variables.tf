variable "table_name" {
  description = "DynamoDB table name"
  type        = string
}

variable "billing_mode" {
  description = "Billing mode (PAY_PER_REQUEST or PROVISIONED)"
  type        = string
  default     = "PAY_PER_REQUEST"
}

variable "hash_key" {
  description = "Hash key attribute name"
  type        = string
}

variable "range_key" {
  description = "Range key attribute name"
  type        = string
  default     = null
}

variable "attributes" {
  description = "List of attribute definitions"
  type = list(object({
    name = string
    type = string
  }))
}

variable "ttl_enabled" {
  description = "Enable TTL on the table"
  type        = bool
  default     = true
}

variable "ttl_attribute_name" {
  description = "TTL attribute name"
  type        = string
  default     = "ttl"
}

variable "point_in_time_recovery" {
  description = "Enable point-in-time recovery"
  type        = bool
  default     = true
}

variable "encryption_enabled" {
  description = "Enable server-side encryption"
  type        = bool
  default     = true
}

variable "kms_key_arn" {
  description = "KMS key ARN for encryption"
  type        = string
  default     = null
}

variable "read_capacity" {
  description = "Read capacity units (provisioned mode)"
  type        = number
  default     = 5
}

variable "write_capacity" {
  description = "Write capacity units (provisioned mode)"
  type        = number
  default     = 5
}

variable "autoscaling_max_read_capacity" {
  description = "Maximum read capacity for autoscaling"
  type        = number
  default     = 100
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "seed_items" {
  description = "Seed items to insert into the table"
  type        = map(string)
  default     = {}
}
