terraform {
  required_version = ">= 1.10.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0" # Семантичне версіонування: будь-яка 5.x.x 
    }
  }

  backend "s3" {
    bucket  = "tf-state-lab5-paid-account-01" # ВКАЖІТЬ СВІЙ БАКЕТ 
    key     = "envs/dev/terraform.tfstate"
    region  = "eu-central-1"
    encrypt = true
    # Нативне блокування S3 (замінює DynamoDB, Terraform >= 1.10.0) 
    use_lockfile = true
  }
}