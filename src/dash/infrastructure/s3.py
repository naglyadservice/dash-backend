from dataclasses import dataclass
from typing import BinaryIO

import aioboto3
from botocore.exceptions import ClientError
from structlog import get_logger

from dash.main.config import S3Config
from dash.services.common.errors.base import ApplicationError

logger = get_logger()


@dataclass
class S3UploadError(ApplicationError):
    message: str = "Error while uploading file. Please, try again later"


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
            raise S3UploadError

    async def delete_file(self, key: str) -> None:
        try:
            async with self.session.client("s3") as client:  # type: ignore
                await client.delete_object(Bucket=self.config.bucket_name, Key=key)
        except ClientError as e:
            logger.error("Failed to delete file from S3", error=e)
            raise S3UploadError
