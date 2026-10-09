import re
from typing import Tuple, Dict, Any
from werkzeug.datastructures import FileStorage
from config.settings import Config
from .errors import ValidationError


VALID_PRIORITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
VALID_STATUSES = {"pending", "completed"}
VALID_CATEGORIES = {
    "College",
    "Work",
    "Personal",
    "Shopping",
    "Health",
    "Finance",
    "Meeting",
    "Study",
    "Other",
}


def validate_audio_file(file: FileStorage) -> Tuple[bool, str]:
    """
    Validates uploaded audio file:
    1. Checks if file is provided.
    2. Checks non-empty filename.
    3. Checks extension against allowed audio list.
    4. Checks file size against configured MAX_AUDIO_SIZE_MB limit.
    """
    if not file or not file.filename:
        raise ValidationError("No audio file provided in request")

    filename = file.filename.lower()
    ext = filename.rsplit(".", 1)[-1] if "." in filename else ""

    if ext not in Config.ALLOWED_AUDIO_EXTENSIONS:
        raise ValidationError(
            f"Unsupported audio format '{ext}'. Allowed formats: {', '.join(sorted(Config.ALLOWED_AUDIO_EXTENSIONS))}"
        )

    # Check file size by seeking to end
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Rewind to start for subsequent reads

    if file_size == 0:
        raise ValidationError("Uploaded audio file is empty (0 bytes)")

    if file_size > Config.MAX_AUDIO_BYTES:
        raise ValidationError(
            f"Audio file size ({file_size / (1024*1024):.1f} MB) exceeds maximum allowed limit of {Config.MAX_AUDIO_SIZE_MB} MB"
        )

    return True, ext


def validate_task_payload(data: Dict[str, Any], is_update: bool = False) -> Dict[str, Any]:
    """
    Validates and normalizes task creation or update payload.
    Returns cleaned data dictionary.
    """
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a valid JSON object")

    cleaned = {}

    # Title validation
    if "title" in data or not is_update:
        title = data.get("title", "").strip() if data.get("title") else ""
        if not title:
            raise ValidationError("Task 'title' is required and cannot be blank")
        if len(title) > 200:
            raise ValidationError("Task 'title' cannot exceed 200 characters")
        cleaned["title"] = title

    # Description (optional)
    if "description" in data:
        desc = data.get("description", "")
        cleaned["description"] = desc.strip() if isinstance(desc, str) else ""

    # Priority validation
    if "priority" in data:
        priority = str(data["priority"]).upper().strip()
        if priority not in VALID_PRIORITIES:
            raise ValidationError(
                f"Invalid priority '{priority}'. Must be one of: {', '.join(sorted(VALID_PRIORITIES))}"
            )
        cleaned["priority"] = priority
    elif not is_update:
        cleaned["priority"] = "MEDIUM"

    # Urgency validation
    if "urgent" in data:
        val = data["urgent"]
        if isinstance(val, bool):
            cleaned["urgent"] = val
        elif isinstance(val, str):
            cleaned["urgent"] = val.lower() in ("true", "1", "yes")
        else:
            cleaned["urgent"] = bool(val)
    elif not is_update:
        cleaned["urgent"] = False

    # Status validation
    if "status" in data:
        status = str(data["status"]).lower().strip()
        if status not in VALID_STATUSES:
            raise ValidationError(
                f"Invalid status '{status}'. Must be one of: {', '.join(sorted(VALID_STATUSES))}"
            )
        cleaned["status"] = status
    elif not is_update:
        cleaned["status"] = "pending"

    # Category validation
    if "category" in data:
        cat = str(data.get("category", "")).strip().capitalize()
        cleaned["category"] = cat if cat else "Other"
    elif not is_update:
        cleaned["category"] = "Other"

    # Due Date validation (YYYY-MM-DD or empty)
    if "due_date" in data:
        due_date = data.get("due_date")
        if due_date:
            due_date = str(due_date).strip()
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", due_date):
                raise ValidationError("Invalid due_date format. Must be YYYY-MM-DD (e.g., 2026-10-15)")
            cleaned["due_date"] = due_date
        else:
            cleaned["due_date"] = None
    elif not is_update:
        cleaned["due_date"] = None

    # Due Time validation (HH:MM or empty)
    if "due_time" in data:
        due_time = data.get("due_time")
        if due_time:
            due_time = str(due_time).strip()
            if not re.match(r"^\d{2}:\d{2}$", due_time):
                raise ValidationError("Invalid due_time format. Must be 24-hour HH:MM (e.g., 17:00)")
            cleaned["due_time"] = due_time
        else:
            cleaned["due_time"] = None
    elif not is_update:
        cleaned["due_time"] = None

    # Estimated duration (minutes)
    if "estimated_duration_minutes" in data:
        duration = data.get("estimated_duration_minutes")
        if duration is not None and duration != "":
            try:
                duration_int = int(duration)
                if duration_int < 0:
                    raise ValueError()
                cleaned["estimated_duration_minutes"] = duration_int
            except ValueError:
                raise ValidationError("estimated_duration_minutes must be a non-negative integer")
        else:
            cleaned["estimated_duration_minutes"] = None

    # Raw transcription tracking (optional)
    if "raw_transcription" in data:
        cleaned["raw_transcription"] = str(data.get("raw_transcription", ""))

    # Detected language tracking (optional)
    if "detected_language" in data:
        cleaned["detected_language"] = str(data.get("detected_language", "English"))

    return cleaned
