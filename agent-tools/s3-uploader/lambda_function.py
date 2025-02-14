import json
import os
import re
import boto3
import mimetypes

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """
    AWS Lambda function to upload a file to S3.

    Expected Input:
    {
        "path": "s3://bucket-name/uploads/testfile.md",
        "content": "This is a test content"
    }

    Returns:
    {
        "message": "File uploaded successfully",
        "public_url": "https://bucket-name.s3.amazonaws.com/uploads/testfile.md"
    }
    """
    try:
        # Extract parameters from event
        s3_path = event.get("path")  # Example: "s3://my-bucket/uploads/testfile.md"
        file_content = event.get("content")

        if not s3_path or not file_content:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing 'path' or 'content' parameter"})
            }

        # Extract bucket name and object key from s3_path
        match = re.match(r"s3://([^/]+)/(.+)", s3_path)
        if not match:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid S3 path format"})
            }

        bucket_name, s3_key = match.groups()

        # Guess MIME type based on file extension
        content_type, _ = mimetypes.guess_type(s3_key)

        # Override Markdown files to use text/plain to force browser display
        if s3_key.endswith(".md"):
            content_type = "text/plain"

        # Upload file to S3 with proper headers
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
                "message": f"File uploaded successfully",
                "public_url": public_url,
                "content_type": content_type
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
