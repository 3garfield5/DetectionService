import os
import boto3
from botocore.client import Config

S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_BUCKET = os.getenv("S3_BUCKET")
S3_SECURE = os.getenv("S3_SECURE", "false").lower() == "true"

session = boto3.session.Session()

s3_client = session.client(
    service_name="s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    config=Config(signature_version="s3v4"),
    verify=S3_SECURE,
)

def upload_file(local_path: str, object_name: str) -> str:
    """
    Загружает файл в MinIO и возвращает public URL
    """
    s3_client.upload_file(
        Filename=local_path,
        Bucket=S3_BUCKET,
        Key=object_name,
        ExtraArgs={"ContentType": "image/jpeg"},
    )

    return f"{S3_ENDPOINT}/{S3_BUCKET}/{object_name}"
