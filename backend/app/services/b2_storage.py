import os
from pathlib import Path

from dotenv import load_dotenv
import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError


load_dotenv()


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


# 8 MB parts
MULTIPART_PART_SIZE = 8 * 1024 * 1024


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

    config = Config(
        connect_timeout=30,
        read_timeout=300,
        retries={
            "max_attempts": 3,
            "mode": "standard",
        },
    )

    return boto3.client(
        "s3",
        endpoint_url=B2_ENDPOINT,
        aws_access_key_id=B2_KEY_ID,
        aws_secret_access_key=B2_APPLICATION_KEY,
        region_name=B2_REGION,
        config=config,
    )


def upload_file(
    local_path: str | Path,
    object_key: str,
    content_type: str = "application/octet-stream",
) -> str:

    path = Path(local_path)

    if not path.exists() or not path.is_file():
        raise FileNotFoundError(
            f"Local file not found: {path}"
        )

    file_size = path.stat().st_size

    print(
        f"[B2 UPLOAD] Starting upload: "
        f"{path.name} ({file_size:,} bytes)"
    )

    print(
        f"[B2 UPLOAD] Bucket: {B2_BUCKET_NAME}"
    )

    print(
        f"[B2 UPLOAD] Key: {object_key}"
    )

    client = _get_client()

    # Small files: normal PUT
    if file_size <= MULTIPART_PART_SIZE:
        print(
            "[B2 UPLOAD] Small file -> single PUT"
        )

        with path.open("rb") as file_obj:
            client.put_object(
                Bucket=B2_BUCKET_NAME,
                Key=object_key,
                Body=file_obj,
                ContentType=content_type,
                ContentLength=file_size,
            )

        print(
            f"[B2 UPLOAD] Upload successful: {object_key}"
        )

        return object_key

    # Large files: multipart upload
    print(
        f"[B2 UPLOAD] Large file -> multipart upload"
    )

    print(
        f"[B2 UPLOAD] Part size: "
        f"{MULTIPART_PART_SIZE:,} bytes"
    )

    multipart = None

    try:
        # Start multipart upload
        print(
            "[B2 UPLOAD] Creating multipart upload..."
        )

        response = client.create_multipart_upload(
            Bucket=B2_BUCKET_NAME,
            Key=object_key,
            ContentType=content_type,
        )

        upload_id = response["UploadId"]

        multipart = {
            "UploadId": upload_id,
            "Parts": [],
        }

        print(
            f"[B2 UPLOAD] Multipart upload created: "
            f"{upload_id}"
        )

        part_number = 1

        with path.open("rb") as file_obj:

            while True:

                data = file_obj.read(
                    MULTIPART_PART_SIZE
                )

                if not data:
                    break

                current_size = len(data)

                print(
                    f"[B2 UPLOAD] Uploading part "
                    f"{part_number} "
                    f"({current_size:,} bytes)..."
                )

                response = client.upload_part(
                    Bucket=B2_BUCKET_NAME,
                    Key=object_key,
                    UploadId=upload_id,
                    PartNumber=part_number,
                    Body=data,
                    ContentLength=current_size,
                )

                etag = response.get("ETag")

                if not etag:
                    raise RuntimeError(
                        f"B2 did not return ETag "
                        f"for part {part_number}"
                    )

                multipart["Parts"].append(
                    {
                        "ETag": etag,
                        "PartNumber": part_number,
                    }
                )

                print(
                    f"[B2 UPLOAD] Part "
                    f"{part_number} successful"
                )

                part_number += 1

        print(
            f"[B2 UPLOAD] Uploaded "
            f"{len(multipart['Parts'])} parts"
        )

        print(
            "[B2 UPLOAD] Completing multipart upload..."
        )

        client.complete_multipart_upload(
            Bucket=B2_BUCKET_NAME,
            Key=object_key,
            UploadId=upload_id,
            MultipartUpload={
                "Parts": multipart["Parts"]
            },
        )

        print(
            f"[B2 UPLOAD] Multipart upload successful: "
            f"{object_key}"
        )

        return object_key

    except Exception as exc:

        print(
            f"[B2 UPLOAD] Upload failed: "
            f"{type(exc).__name__}: {exc}"
        )

        # Abort incomplete multipart upload
        if multipart is not None:

            try:
                print(
                    "[B2 UPLOAD] Aborting incomplete "
                    "multipart upload..."
                )

                client.abort_multipart_upload(
                    Bucket=B2_BUCKET_NAME,
                    Key=object_key,
                    UploadId=multipart["UploadId"],
                )

                print(
                    "[B2 UPLOAD] Multipart upload aborted"
                )

            except Exception as abort_exc:

                print(
                    "[B2 UPLOAD] Abort failed: "
                    f"{type(abort_exc).__name__}: "
                    f"{abort_exc}"
                )

        raise


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

