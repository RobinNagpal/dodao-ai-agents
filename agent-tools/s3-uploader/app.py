from chalice import Chalice, Response
import boto3
import json
import re
import mimetypes

app = Chalice(app_name="s3-uploader")
s3 = boto3.client('s3')

@app.lambda_function()
def upload_to_s3(event, context):
    try:
        # Extract payload
        body = json.loads(event.get("body", "{}"))
        s3_path = body.get("path")  # Example: "s3://bucket-381-131/uploads/testfile2.md"
        file_content = body.get("content")

        if not s3_path or not file_content:
            return {"statusCode": 400, "body": json.dumps({"error": "Missing s3_path or file_content"})}

        # Extract bucket name and object key from s3_path
        match = re.match(r"s3://([^/]+)/(.+)", s3_path)
        if not match:
            return {"statusCode": 400, "body": json.dumps({"error": "Invalid S3 path format"})}

        bucket_name, s3_key = match.groups()

        # Force Markdown files to use text/markdown Content-Type
        content_type, _ = mimetypes.guess_type(s3_key)
        if s3_key.endswith(".md"):
            content_type = "text/plain"  # Ensure Markdown opens in browser

        # Upload to S3 with proper headers
        s3.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=file_content,
            ACL="public-read",
            ContentType=content_type,
        )

        # Public URL of the uploaded object
        public_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"Uploaded to {s3_path}",
                "public_url": public_url,
                "content_type": content_type
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
