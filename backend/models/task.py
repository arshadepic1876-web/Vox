import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any
from config.settings import Config


def get_current_timestamp() -> str:
    """Returns current ISO formatted timestamp in the configured timezone."""
    try:
        tz = ZoneInfo(Config.TIMEZONE)
        return datetime.now(tz).isoformat()
    except Exception:
        return datetime.now().isoformat()


class Task:
    """
    Core Domain Model for a Task.
    Represents a structured task item across the application and storage layers.
    """

    def __init__(
        self,
        title: str,
        description: str = "",
        due_date: Optional[str] = None,
        due_time: Optional[str] = None,
        priority: str = "MEDIUM",
        urgent: bool = False,
        category: str = "Other",
        status: str = "pending",
        estimated_duration_minutes: Optional[int] = None,
        raw_transcription: str = "",
        task_id: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ):
        self.task_id = task_id or str(uuid.uuid4())
        self.title = title
        self.description = description
        self.due_date = due_date
        self.due_time = due_time
        self.priority = priority.upper()
        self.urgent = urgent
        self.category = category.capitalize() if category else "Other"
        self.status = status.lower()
        self.estimated_duration_minutes = estimated_duration_minutes
        self.raw_transcription = raw_transcription
        self.created_at = created_at or get_current_timestamp()
        self.updated_at = updated_at or self.created_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert task instance to dictionary for JSON API responses and DB storage."""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date,
            "due_time": self.due_time,
            "priority": self.priority,
            "urgent": self.urgent,
            "category": self.category,
            "status": self.status,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "raw_transcription": self.raw_transcription,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Instantiate a Task model from a dictionary."""
        return cls(
            task_id=data.get("task_id"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            due_date=data.get("due_date"),
            due_time=data.get("due_time"),
            priority=data.get("priority", "MEDIUM"),
            urgent=data.get("urgent", False),
            category=data.get("category", "Other"),
            status=data.get("status", "pending"),
            estimated_duration_minutes=data.get("estimated_duration_minutes"),
            raw_transcription=data.get("raw_transcription", ""),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def mark_completed(self) -> None:
        """Mark task as completed and update timestamp."""
        self.status = "completed"
        self.updated_at = get_current_timestamp()

    def mark_pending(self) -> None:
        """Mark task as pending and update timestamp."""
        self.status = "pending"
        self.updated_at = get_current_timestamp()

    def update(self, fields: Dict[str, Any]) -> None:
        """Update allowed fields on task and refresh updated_at."""
        for field in [
            "title",
            "description",
            "due_date",
            "due_time",
            "priority",
            "urgent",
            "category",
            "status",
            "estimated_duration_minutes",
        ]:
            if field in fields:
                setattr(self, field, fields[field])
        self.updated_at = get_current_timestamp()
