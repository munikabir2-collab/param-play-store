import os
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError


B2_KEY_ID = os.getenv("B2_KEY_ID")
B2_APPLICATION_KEY = os.getenv("B2_APPLICATION_KEY")
B2_BUCKET_NAME = os.getenv(
    "B2_BUCKET_NAME",
    "param-play-store-apps",
)
B2_ENDPOINT = os.getenv("B2_ENDPOINT")
B2_REGION = os.getenv(
    "B2_REGION",
    "us-east-005",
)


def _get_client():
    if not B2_KEY_ID:
        raise RuntimeError(
            "B2_KEY_ID environment variable missing"
        )

    if not B2_APPLICATION_KEY:
        raise RuntimeError(
            "B2_APPLICATION_KEY environment variable missing"
        )

    if not B2_ENDPOINT:
        raise RuntimeError(
            "B2_ENDPOINT environment variable missing"
        )

    return boto3.client(
        "s3",
        endpoint_url=B2_ENDPOINT,
        aws_access_key_id=B2_KEY_ID,
        aws_secret_access_key=B2_APPLICATION_KEY,
        region_name=B2_REGION,
    )


def upload_file(
    local_path: str | Path,
    object_key: str,
    content_type: str = "application/octet-stream",
) -> str:

    client = _get_client()

    path = Path(local_path)

    if not path.exists() or not path.is_file():
        raise FileNotFoundError(
            f"Local file not found: {path}"
        )

    client.upload_file(
        str(path),
        B2_BUCKET_NAME,
        object_key,
        ExtraArgs={
            "ContentType": content_type,
        },
    )

    return object_key


def download_file(object_key: str):
    client = _get_client()

    return client.get_object(
        Bucket=B2_BUCKET_NAME,
        Key=object_key,
    )


def delete_file(object_key: str | None) -> bool:

    if not object_key:
        return False

    client = _get_client()

    try:
        client.delete_object(
            Bucket=B2_BUCKET_NAME,
            Key=object_key,
        )

        return True

    except (BotoCoreError, ClientError):
        return False


def file_exists(object_key: str) -> bool:

    client = _get_client()

    try:
        client.head_object(
            Bucket=B2_BUCKET_NAME,
            Key=object_key,
        )

        return True

    except (BotoCoreError, ClientError):
        return False