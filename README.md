# Serverless Page View Counter

A serverless REST API built on AWS that tracks page view counts per URL. Built with AWS Lambda, API Gateway, DynamoDB, and S3. Infrastructure managed via Terraform.

## Architecture

```
Client → API Gateway → Lambda → DynamoDB (views)
                          ↓
                        S3 (request logs)
```

| Component | Resource | Purpose |
|---|---|---|
| API Gateway | `bodruh-petro-01-http-api` | HTTP routing, `ANY /{proxy+}` |
| Lambda | `bodruh-petro-01-api-handler` | Business logic, Python 3.12 |
| DynamoDB | `bodruh-petro-01-views` | View counters per page |
| S3 | `bodruh-petro-01-logs` | Per-request JSON logs |

## API

### GET /views/{page_id}
Returns the current view count for a page.

**Request:**
```bash
curl https://<api-id>.execute-api.eu-central-1.amazonaws.com/views/home
```

**Response:**
```json
{
  "page_id": "home",
  "views": 42
}
```

> Returns `views: 0` if the page has never been visited.

---

### POST /views/{page_id}
Atomically increments the view counter by 1.

**Request:**
```bash
curl -X POST https://<api-id>.execute-api.eu-central-1.amazonaws.com/views/home
```

**Response:**
```json
{
  "page_id": "home",
  "views": 43
}
```

> Uses DynamoDB `ADD` operation — safe under concurrent requests, no race conditions.

---

## DynamoDB Schema

Table: `bodruh-petro-01-views`  
Billing: PAY_PER_REQUEST (on-demand)

| Attribute | Type | Role |
|---|---|---|
| `page_id` | String | Partition key |
| `views` | Number | Counter (auto-created on first POST) |

## S3 Log Format

Each request writes one JSON file to `logs/{page_id}/{uuid}.json`:

```json
{
  "method": "POST",
  "page_id": "home",
  "timestamp": "2026-03-29T17:00:00.000Z",
  "status_code": 200
}
```

Logs are automatically deleted after **30 days** via S3 lifecycle policy.

---

## Project Structure

```
.
├── src/
│   └── app.py                        # Lambda handler
├── modules/
│   ├── lambda/main.tf                # Lambda + IAM
│   ├── api_gateway/main.tf           # API Gateway v2
│   ├── dynamodb/main.tf              # DynamoDB table
│   └── s3/main.tf                    # S3 logs bucket
└── envs/
    └── dev/
        ├── main.tf                   # Module wiring
        └── backend.tf                # Remote state (S3)
```

## Infrastructure

### Prerequisites
- Terraform >= 1.10.0
- AWS CLI configured
- S3 bucket for Terraform state

### Deploy

```bash
cd envs/dev
terraform init
terraform apply
```

### Destroy

```bash
terraform destroy
```

> **Note:** `force_destroy = true` is set on the S3 logs bucket, so it will be deleted even if it contains log files.

---

## Environment Variables (Lambda)

| Variable | Description |
|---|---|
| `TABLE_NAME` | DynamoDB table name |
| `LOG_BUCKET` | S3 bucket name for request logs |

## IAM Permissions

Lambda execution role has the minimum required permissions:

| Action | Resource |
|---|---|
| `dynamodb:GetItem` | views table |
| `dynamodb:UpdateItem` | views table |
| `s3:PutObject` | `logs/*` prefix in logs bucket |
| CloudWatch Logs | via `AWSLambdaBasicExecutionRole` |
