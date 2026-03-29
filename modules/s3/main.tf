variable "bucket_name" { type = string }

resource "aws_s3_bucket" "logs" {
  bucket        = var.bucket_name
  force_destroy = true
}

resource "aws_s3_bucket_lifecycle_configuration" "logs_lifecycle" {
  bucket = aws_s3_bucket.logs.id

  rule {
    id     = "delete-old-logs"
    status = "Enabled"

    filter {}

    expiration {
      days = 30
    }
  }
}

output "bucket_name" { value = aws_s3_bucket.logs.bucket }
output "bucket_arn"  { value = aws_s3_bucket.logs.arn }

