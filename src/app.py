import json
import boto3
import os
import uuid
from datetime import datetime

TABLE_NAME = os.environ.get("TABLE_NAME")
LOG_BUCKET = os.environ.get("LOG_BUCKET")

if not TABLE_NAME:
    raise ValueError("TABLE_NAME environment variable is not set")
if not LOG_BUCKET:
    raise ValueError("LOG_BUCKET environment variable is not set")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)
s3 = boto3.client("s3")


def log_request(method, page_id, status_code):
    log = {
        "method": method,
        "page_id": page_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status_code": status_code,
    }
    s3.put_object(
        Bucket=LOG_BUCKET,
        Key=f"logs/{page_id}/{uuid.uuid4()}.json",
        Body=json.dumps(log),
        ContentType="application/json",
    )


def handler(event, context):
    http_method = event["requestContext"]["http"]["method"]

    # Витягуємо page_id з шляху /views/{page_id}
    path = event["requestContext"]["http"]["path"]  # наприклад /views/1
    path_parts = path.strip("/").split("/")         # ["views", "1"]

    if len(path_parts) < 2 or path_parts[0] != "views":
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Invalid path. Use /views/{page_id}"}),
        }

    page_id = path_parts[1]
    status_code = 200

    try:
        if http_method == "GET":
            response = table.get_item(Key={"page_id": page_id})
            views = response.get("Item", {}).get("views", 0)

            result = {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"page_id": page_id, "views": int(views)}),
            }

        elif http_method == "POST":
            response = table.update_item(
                Key={"page_id": page_id},
                UpdateExpression="ADD #v :inc",
                ExpressionAttributeNames={"#v": "views"},
                ExpressionAttributeValues={":inc": 1},
                ReturnValues="UPDATED_NEW",
            )
            views = response["Attributes"]["views"]

            result = {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"page_id": page_id, "views": int(views)}),
            }

        else:
            status_code = 405
            result = {
                "statusCode": 405,
                "body": json.dumps({"message": "Method Not Allowed"}),
            }

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        status_code = 500
        result = {
            "statusCode": 500,
            "body": json.dumps({"message": "Internal Server Error", "detail": str(e)}),
        }

    finally:
        try:
            log_request(http_method, page_id, status_code)
        except Exception as log_err:
            print(f"Logging error: {log_err}")

    return result