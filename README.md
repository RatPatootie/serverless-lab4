# Project Setup Guide

This project uses **Terraform** to deploy serverless infrastructure and AI services on **AWS**. Follow these steps to initialize and deploy the project.

## 1. Prerequisites
Before you begin, ensure you have the following installed and configured:
* **Terraform**: [Download here](https://www.terraform.io/downloads)
* **AWS CLI**: [Download here](https://aws.amazon.com/cli/)
* **AWS Credentials**: Run `aws configure` to set up your Access Key, Secret Key, and default region.

## 2. Infrastructure Configuration
To manage the Terraform state remotely, you need an S3 bucket.

1.  **Create a Bucket**: Create a unique S3 bucket in your AWS Console (e.g., `my-terraform-state-bucket`).
2.  **Update Backend**: Open `backend.tf` and replace the placeholder bucket name with your actual bucket name:
    ```hcl
    terraform {
      backend "s3" {
        bucket = "YOUR_BUCKET_NAME_HERE"
        key    = "state/terraform.tfstate"
        region = "us-east-1"
      }
    }
    ```

## 3. Deployment Steps
Navigate to the project root directory in your terminal and run:

### A. Initialize Terraform
This downloads the necessary AWS providers and initializes the S3 backend.
```bash
terraform init
```

### B. View Execution Plan
Check what resources will be created before applying changes.
```bash
terraform plan
```

### C. Apply Changes
Deploy the infrastructure to AWS. Type `yes` when prompted.
```bash
terraform apply
```



## 4. Cleaning Up
To avoid incurring AWS costs after you are finished, destroy all created resources:
```bash
terraform destroy
```
