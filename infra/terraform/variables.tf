variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "artifact_bucket_name" {
  description = "Globally unique S3 bucket name for MLflow artifacts"
  type        = string
  default     = "taskly-mlflow-artifacts-686699774218-us-east-1"
}
