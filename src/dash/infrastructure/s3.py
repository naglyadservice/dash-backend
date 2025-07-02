from typing import BinaryIO

import aioboto3
from botocore.exceptions import ClientError
from structlog import get_logger

from dash.main.config import S3Config

logger = get_logger()


class S3UploadError(Exception):
    def __str__(self) -> str:
        return "Something went wrong. Please try again later"


class S3Service:
    def __init__(self, config: S3Config) -> None:
        self.session = aioboto3.Session()
        self.config = config

    async def upload_file(self, file_content: BinaryIO, key: str) -> None:
        try:
            async with self.session.client("s3") as client:  # type: ignore
                await client.upload_fileobj(file_content, self.config.bucket_name, key)
        except ClientError as e:
            logger.error("Failed to upload file to S3", error=e)
            raise S3UploadError()
