import os
import boto3

s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_DEFAULT_REGION")
)
BUCKET_NAME = os.getenv("S3_BUCKET_NAME")


def upload_to_s3(content, s3_key, content_type="text/plain"):
    """
    Uploads content to S3.
    """
    print(f"Uploading to S3... at s3://{BUCKET_NAME}/{s3_key} with content type {content_type}")
    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=f"crowd-fund-analysis/{s3_key}",
        Body=content,
        ContentType=content_type,
        ACL="public-read",
    )
    print(f"Uploaded to s3://{BUCKET_NAME}/{s3_key}")

def upload_to_s3_public_equities(content, s3_key: str, content_type="text/plain"):
    """
    Uploads content to S3.
    """
    print(f"Uploading to S3... at s3://{BUCKET_NAME}/{s3_key} with content type {content_type}")
    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=f"public-equities/US/gics/{s3_key}",
        Body=content,
        ContentType=content_type,
        ACL="public-read",
    )
    print(f"Uploaded to s3://{BUCKET_NAME}/US/{s3_key}")
