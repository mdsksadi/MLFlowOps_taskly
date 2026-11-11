provider "aws" {
  region = var.aws_region
}

resource "aws_s3_bucket" "mlflow_artifacts" {
  bucket = var.artifact_bucket_name

  tags = {
    Project   = "Taskly"
    Purpose   = "MLflow Artifacts"
    ManagedBy = "Terraform"
  }
}

resource "aws_s3_bucket_versioning" "mlflow_artifacts" {
  bucket = aws_s3_bucket.mlflow_artifacts.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "mlflow_artifacts" {
  bucket = aws_s3_bucket.mlflow_artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "mlflow_artifacts" {
  bucket = aws_s3_bucket.mlflow_artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

output "artifact_bucket_name" {
  value = aws_s3_bucket.mlflow_artifacts.bucket
}

output "artifact_bucket_arn" {
  value = aws_s3_bucket.mlflow_artifacts.arn
}
