# envs/dev/main.tf 
provider "aws" {
  region = "eu-central-1"
}
locals {
  # ЗАМІНІТЬ НА ВЛАСНИЙ ПРЕФІКС: Прізвище-Імя-Варіант 
  prefix = "paid-account-01"
}
# Виклик модуля бази даних 
module "database" {
  source     = "../../modules/dynamodb"
  table_name = "${local.prefix}-table"
}

# Виклик модуля обчислень з передачею ARN та імені таблиці 
module "backend" {
  source              = "../../modules/lambda"
  function_name       = "${local.prefix}-api-handler"
  source_file         = "${path.root}/../../src/app.py"
  dynamodb_table_arn  = module.database.table_arn
  dynamodb_table_name = module.database.table_name
  log_bucket_name     = module.logs_bucket.bucket_name
  log_bucket_arn      = module.logs_bucket.bucket_arn 
}

# Виклик модуля шлюзу API 
module "api" {
  source               = "../../modules/api_gateway"
  api_name             = "${local.prefix}-http-api"
  lambda_invoke_arn    = module.backend.invoke_arn
  lambda_function_name = module.backend.function_name
}
module "logs_bucket" {
  source      = "../../modules/s3"
  bucket_name = "paid-account-01-logs"
}

# Вивід URL розгорнутого API (використовується у кроці 6) 
output "api_url" {
  value = module.api.api_endpoint
} 