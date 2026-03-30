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

# AWS clients (module level as required)
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

s3 = boto3.client("s3")
comprehend = boto3.client("comprehend")


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

    path = event["requestContext"]["http"]["path"]
    path_parts = path.strip("/").split("/")

    if len(path_parts) < 2 or path_parts[0] != "views":
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Invalid path. Use /views/{page_id}"}),
        }

    page_id = path_parts[1]
    status_code = 200
    result = None

    try:
        # =========================
        # NEW ENDPOINT:
        # POST /views/{id}/analyze
        # =========================
        if http_method == "POST" and len(path_parts) == 3 and path_parts[2] == "analyze":

            body = json.loads(event.get("body", "{}"))
            text = body.get("text")

            if not text:
                status_code = 400
                result = {
                    "statusCode": 400,
                    "body": json.dumps({"message": "Missing 'text' in request body"}),
                }

            else:
                try:
                    ai_response = comprehend.detect_sentiment(
                        Text=text,
                        LanguageCode="en"
                    )

                    sentiment = ai_response["Sentiment"]
                    sentiment_score = ai_response["SentimentScore"]

                    table.update_item(
                        Key={"page_id": page_id},
                        UpdateExpression="SET sentiment = :s, sentiment_score = :sc",
                        ExpressionAttributeValues={
                            ":s": sentiment,
                            ":sc": sentiment_score,
                        },
                    )

                    status_code = 200
                    result = {
                        "statusCode": 200,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps({
                            "page_id": page_id,
                            "sentiment": sentiment,
                            "score": sentiment_score,
                        }),
                    }

                except Exception as ai_err:
                    print(f"Comprehend error: {ai_err}")

                    # graceful degradation
                    status_code = 200
                    result = {
                        "statusCode": 200,
                        "body": json.dumps({
                            "page_id": page_id,
                            "message": "AI analysis failed, but request processed",
                        }),
                    }

        # =========================
        # GET /views/{id}
        # =========================
        elif http_method == "GET":
            response = table.get_item(Key={"page_id": page_id})
            views = response.get("Item", {}).get("views", 0)

            status_code = 200
            result = {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"page_id": page_id, "views": int(views)}),
            }

        # =========================
        # POST /views/{id}
        # =========================
        elif http_method == "POST":
            response = table.update_item(
                Key={"page_id": page_id},
                UpdateExpression="ADD #v :inc",
                ExpressionAttributeNames={"#v": "views"},
                ExpressionAttributeValues={":inc": 1},
                ReturnValues="UPDATED_NEW",
            )

            views = response["Attributes"]["views"]

            status_code = 200
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
            "body": json.dumps({
                "message": "Internal Server Error",
                "detail": str(e),
            }),
        }

    finally:
        try:
            log_request(http_method, page_id, status_code)
        except Exception as log_err:
            print(f"Logging error: {log_err}")

    return result