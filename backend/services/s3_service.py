import logging
from pathlib import Path
from typing import Optional
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from config.settings import Config
from utils.errors import AWSIntegrationError

logger = logging.getLogger(__name__)


class S3Service:
    """
    Manages transient audio uploads and immediate cleanup in Amazon S3.
    """

    def __init__(self):
        self.bucket_name = Config.S3_BUCKET_NAME
        self.region = Config.AWS_REGION
        self._s3_client = None

    @property
    def client(self):
        """Lazy initialization of boto3 S3 client."""
        if self._s3_client is None:
            # Use explicit credentials if set in .env; otherwise boto3 automatically
            # falls back to EC2 IAM Instance Profile or ~/.aws/credentials
            session_kwargs = {"region_name": self.region}
            if Config.AWS_ACCESS_KEY_ID and Config.AWS_SECRET_ACCESS_KEY:
                session_kwargs["aws_access_key_id"] = Config.AWS_ACCESS_KEY_ID
                session_kwargs["aws_secret_access_key"] = Config.AWS_SECRET_ACCESS_KEY

            self._s3_client = boto3.client("s3", **session_kwargs)
        return self._s3_client

    def is_configured(self) -> bool:
        """Check if S3 bucket and region are defined."""
        return bool(self.bucket_name and self.region)

    def upload_audio(self, local_file_path: Path, object_key: str) -> str:
        """
        Uploads local audio file to private S3 bucket.
        Returns the s3:// URI required by Amazon Transcribe.
        """
        if not self.is_configured():
            logger.warning("AWS S3 is not configured. Running in local storage mode.")
            return str(local_file_path)

        local_path = Path(local_file_path)
        if not local_path.exists():
            raise FileNotFoundError(f"Local file does not exist: {local_file_path}")

        try:
            # Determine content type based on file extension
            ext = local_path.suffix.lower().lstrip(".")
            content_type = f"audio/{ext}" if ext in ["webm", "wav", "ogg", "mp4"] else "application/octet-stream"

            logger.info("Uploading %s to s3://%s/%s", local_path.name, self.bucket_name, object_key)
            self.client.upload_file(
                Filename=str(local_path),
                Bucket=self.bucket_name,
                Key=object_key,
                ExtraArgs={"ContentType": content_type},
            )

            s3_uri = f"s3://{self.bucket_name}/{object_key}"
            logger.info("Upload complete: %s", s3_uri)
            return s3_uri

        except (ClientError, BotoCoreError) as err:
            logger.error("S3 upload failed: %s", err)
            raise AWSIntegrationError(f"Failed to upload audio to Amazon S3: {str(err)}")

    def delete_audio(self, object_key: str) -> bool:
        """
        Immediately deletes audio file from S3 once transcription completes
        to eliminate storage fees and protect user privacy.
        """
        if not self.is_configured():
            return True

        try:
            logger.info("Cleaning up transient audio s3://%s/%s", self.bucket_name, object_key)
            self.client.delete_object(Bucket=self.bucket_name, Key=object_key)
            return True
        except (ClientError, BotoCoreError) as err:
            logger.warning("Transient audio cleanup in S3 encountered an error: %s", err)
            return False


# Singleton instance
s3_service = S3Service()
