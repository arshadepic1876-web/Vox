import logging
import time
import uuid
import requests
from typing import Optional
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from config.settings import Config
from utils.errors import AudioProcessingError, AWSIntegrationError

logger = logging.getLogger(__name__)


class TranscribeService:
    """
    Manages Amazon Transcribe speech-to-text batch transcription jobs.
    """

    def __init__(self):
        self.region = Config.AWS_REGION
        self._transcribe_client = None

    @property
    def client(self):
        """Lazy initialization of boto3 Transcribe client."""
        if self._transcribe_client is None:
            session_kwargs = {"region_name": self.region}
            if Config.AWS_ACCESS_KEY_ID and Config.AWS_SECRET_ACCESS_KEY:
                session_kwargs["aws_access_key_id"] = Config.AWS_ACCESS_KEY_ID
                session_kwargs["aws_secret_access_key"] = Config.AWS_SECRET_ACCESS_KEY

            self._transcribe_client = boto3.client("transcribe", **session_kwargs)
        return self._transcribe_client

    def is_configured(self) -> bool:
        """Check if AWS credentials and S3 bucket are active for Transcribe."""
        return bool(Config.S3_BUCKET_NAME and Config.AWS_REGION)

    def transcribe_audio_uri(
        self,
        s3_uri: str,
        media_format: str = "webm",
        language_code: str = "en-US",
        max_wait_seconds: int = 60,
    ) -> str:
        """
        Dispatches an Amazon Transcribe batch job for the audio file in S3,
        polls until completion, and returns the recognized text string.
        """
        if not self.is_configured() or not s3_uri.startswith("s3://"):
            logger.warning("Amazon Transcribe is not active (AWS credentials/bucket not configured in .env).")
            return ""

        job_name = f"vox-task-{uuid.uuid4().hex[:12]}"
        logger.info("Starting Amazon Transcribe job: %s for %s", job_name, s3_uri)

        try:
            # Map extensions to valid Amazon Transcribe MediaFormat values
            format_map = {
                "webm": "webm",
                "wav": "wav",
                "ogg": "ogg",
                "mp4": "mp4",
                "m4a": "mp4",
            }
            clean_format = format_map.get(media_format.lower(), "webm")

            job_params = {
                "TranscriptionJobName": job_name,
                "Media": {"MediaFileUri": s3_uri},
                "MediaFormat": clean_format,
            }

            # Automatic Language Identification across multiple languages
            if not language_code or language_code == "auto":
                job_params["IdentifyLanguage"] = True
                job_params["LanguageOptions"] = [
                    "en-US", "en-IN", "hi-IN", "es-US", "es-ES",
                    "fr-FR", "de-DE", "it-IT", "pt-BR", "ja-JP", "ar-SA"
                ]
            else:
                job_params["LanguageCode"] = language_code

            self.client.start_transcription_job(**job_params)

            # Poll for completion
            start_time = time.time()
            while time.time() - start_time < max_wait_seconds:
                response = self.client.get_transcription_job(TranscriptionJobName=job_name)
                status = response["TranscriptionJob"]["TranscriptionJobStatus"]

                if status == "COMPLETED":
                    transcript_url = response["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
                    logger.info("Transcribe job %s completed. Fetching results...", job_name)
                    
                    # Fetch JSON transcript payload from AWS
                    res = requests.get(transcript_url, timeout=10)
                    res.raise_for_status()
                    data = res.json()
                    
                    transcripts = data.get("results", {}).get("transcripts", [])
                    if transcripts and "transcript" in transcripts[0]:
                        recognized_text = transcripts[0]["transcript"].strip()
                        logger.info("Transcribed text: '%s'", recognized_text)
                        return recognized_text
                    return ""

                elif status == "FAILED":
                    failure_reason = response["TranscriptionJob"].get("FailureReason", "Unknown error")
                    logger.error("Transcribe job %s failed: %s", job_name, failure_reason)
                    raise AudioProcessingError(f"Speech transcription failed: {failure_reason}")

                time.sleep(2)

            raise AudioProcessingError("Transcription request timed out. Please try recording a shorter audio clip.")

        except (ClientError, BotoCoreError) as err:
            logger.error("Amazon Transcribe error: %s", err)
            raise AWSIntegrationError(f"Amazon Transcribe service error: {str(err)}")


# Singleton instance
transcribe_service = TranscribeService()
