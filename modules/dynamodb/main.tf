# modules/dynamodb/main.tf 
 
 
variable "table_name" { 
  description = "The unique name of the DynamoDB table" 
  type        = string 
} 

resource "aws_dynamodb_table" "views" {
  name         = "paid-account-01-views"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "page_id"

  attribute {
    name = "page_id"
    type = "S"
  }
}
 
output "table_name" { 
  value = aws_dynamodb_table.views.name 
} 
 
output "table_arn" { 
  value = aws_dynamodb_table.views.arn 
}