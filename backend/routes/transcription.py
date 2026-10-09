import logging
import uuid
from flask import Blueprint, request, jsonify
from config.settings import Config
from utils.validation import validate_audio_file
from utils.errors import ValidationError, AudioProcessingError
from services.s3_service import s3_service
from services.transcribe_service import transcribe_service
from services.task_parser import task_parser_service

logger = logging.getLogger(__name__)

transcription_bp = Blueprint("transcription", __name__, url_prefix="/api")


@transcription_bp.route("/transcribe", methods=["POST"])
def transcribe_audio_endpoint():
    """
    POST /api/transcribe
    Receives multipart audio file from frontend MediaRecorder,
    processes via Amazon S3 and Amazon Transcribe (with offline fallback),
    extracts structured task parameters using AI Task Parser,
    and returns task preview JSON for user confirmation.
    """
    if "audio" not in request.files:
        raise ValidationError("Missing 'audio' file in multipart request")

    audio_file = request.files["audio"]
    _, ext = validate_audio_file(audio_file)

    # Save to unique local staging file
    file_id = str(uuid.uuid4())
    local_filename = f"{file_id}.{ext}"
    local_path = Config.UPLOADS_DIR / local_filename
    audio_file.save(str(local_path))
    logger.info("Saved incoming audio stream to %s", local_path)

    s3_key = f"recordings/{local_filename}"
    s3_uri = ""

    try:
        # Step 1: Upload to Amazon S3 (if AWS configured)
        if s3_service.is_configured():
            s3_uri = s3_service.upload_audio(local_path, s3_key)
        else:
            s3_uri = str(local_path)

        client_transcript = request.form.get("transcript", "").strip()

        # Step 2: Speech-to-Text via Amazon Transcribe (if configured)
        raw_transcript = ""
        if transcribe_service.is_configured():
            raw_transcript = transcribe_service.transcribe_audio_uri(
                s3_uri=s3_uri,
                media_format=ext,
                language_code=request.form.get("language", "auto"),
            )

        # If AWS Transcribe is not configured or returned empty, use client-recognized speech
        if not raw_transcript and client_transcript:
            logger.info("Using genuine client-recognized speech transcript: '%s'", client_transcript)
            raw_transcript = client_transcript

        if not raw_transcript:
            raise AudioProcessingError(
                "No speech was detected. Please speak clearly into your microphone, or configure AWS Transcribe in backend/.env."
            )

        # Step 3: AI / NLP Task Understanding & Attribute Extraction
        structured_task = task_parser_service.parse_transcription(raw_transcript)

        return (
            jsonify({
                "success": True,
                "message": "Speech transcribed and task parameters extracted successfully",
                "data": structured_task,
            }),
            200,
        )

    finally:
        # Clean up temporary storage:
        # 1. Delete transient audio from Amazon S3
        if s3_service.is_configured():
            s3_service.delete_audio(s3_key)

        # 2. Delete local staging audio file
        try:
            if local_path.exists():
                local_path.unlink()
                logger.info("Deleted local staging audio %s", local_path.name)
        except Exception as e:
            logger.warning("Error deleting local staging file: %s", e)
