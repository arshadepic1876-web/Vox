import os
from pathlib import Path
from dotenv import load_dotenv

# Base backend directory (where app.py and .env live)
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from backend/.env
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)


class Config:
    """
    Centralized configuration management.
    Reads values from environment variables with safe development defaults.
    """

    # Server settings
    PORT = int(os.getenv("PORT", 5000))
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "t")
    TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    # Directories
    BASE_DIR = BASE_DIR
    UPLOADS_DIR = BASE_DIR / "uploads"
    DATA_DIR = BASE_DIR / "data"

    # Audio upload limits
    MAX_AUDIO_SIZE_MB = int(os.getenv("MAX_AUDIO_SIZE_MB", 10))
    MAX_AUDIO_BYTES = MAX_AUDIO_SIZE_MB * 1024 * 1024
    ALLOWED_AUDIO_EXTENSIONS = set(
        os.getenv("ALLOWED_AUDIO_EXTENSIONS", "webm,wav,ogg,mp4,m4a").split(",")
    )

    # Storage backend: 'local' (JSON file) or 'dynamodb' (AWS)
    STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")
    LOCAL_STORAGE_PATH = BASE_DIR / os.getenv("LOCAL_STORAGE_PATH", "data/tasks.json")
    DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "VoxTasks")

    # AWS Credentials and Region
    AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "")

    # AI Task Parser settings
    AI_PARSER_PROVIDER = os.getenv("AI_PARSER_PROVIDER", "rule_based")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

    @classmethod
    def is_aws_configured(cls) -> bool:
        """Check if AWS credentials and bucket name are configured."""
        return bool(cls.S3_BUCKET_NAME and cls.AWS_REGION)

    @classmethod
    def get_public_summary(cls) -> dict:
        """
        Return safe configuration summary without exposing sensitive credentials.
        """
        return {
            "port": cls.PORT,
            "environment": cls.FLASK_ENV,
            "debug": cls.FLASK_DEBUG,
            "timezone": cls.TIMEZONE,
            "max_audio_size_mb": cls.MAX_AUDIO_SIZE_MB,
            "storage_backend": cls.STORAGE_BACKEND,
            "aws_region": cls.AWS_REGION,
            "aws_s3_configured": bool(cls.S3_BUCKET_NAME),
            "ai_parser_provider": cls.AI_PARSER_PROVIDER,
        }
