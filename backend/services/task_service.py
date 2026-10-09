import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from config.settings import Config
from models.task import Task
from utils.errors import NotFoundError, AWSIntegrationError

logger = logging.getLogger(__name__)


class LocalJSONTaskRepository:
    """
    Local JSON file repository adapter.
    Enables zero-cost offline development and local testing.
    """

    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self._write_all([])

    def _read_all(self) -> List[Dict[str, Any]]:
        try:
            if not self.file_path.exists() or self.file_path.stat().st_size == 0:
                return []
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Error reading local tasks file: %s", e)
            return []

    def _write_all(self, tasks: List[Dict[str, Any]]) -> None:
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(tasks, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("Error writing local tasks file: %s", e)
            raise IOError(f"Could not save tasks locally: {e}")

    def get_all(self) -> List[Dict[str, Any]]:
        tasks = self._read_all()
        # Sort newest first by default
        return sorted(tasks, key=lambda t: t.get("created_at", ""), reverse=True)

    def get_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        tasks = self._read_all()
        for t in tasks:
            if t.get("task_id") == task_id:
                return t
        return None

    def save(self, task_dict: Dict[str, Any]) -> Dict[str, Any]:
        tasks = self._read_all()
        existing_idx = next((i for i, t in enumerate(tasks) if t.get("task_id") == task_dict["task_id"]), -1)
        if existing_idx >= 0:
            tasks[existing_idx] = task_dict
        else:
            tasks.insert(0, task_dict)
        self._write_all(tasks)
        return task_dict

    def delete(self, task_id: str) -> bool:
        tasks = self._read_all()
        initial_len = len(tasks)
        tasks = [t for t in tasks if t.get("task_id") != task_id]
        if len(tasks) < initial_len:
            self._write_all(tasks)
            return True
        return False


class DynamoDBTaskRepository:
    """
    Amazon DynamoDB production repository adapter.
    Uses AWS NoSQL table for scalable cloud persistence.
    """

    def __init__(self, table_name: str, region: str):
        self.table_name = table_name
        self.region = region
        self._table = None

    @property
    def table(self):
        if self._table is None:
            session_kwargs = {"region_name": self.region}
            if Config.AWS_ACCESS_KEY_ID and Config.AWS_SECRET_ACCESS_KEY:
                session_kwargs["aws_access_key_id"] = Config.AWS_ACCESS_KEY_ID
                session_kwargs["aws_secret_access_key"] = Config.AWS_SECRET_ACCESS_KEY

            dynamodb = boto3.resource("dynamodb", **session_kwargs)
            self._table = dynamodb.Table(self.table_name)
        return self._table

    def get_all(self) -> List[Dict[str, Any]]:
        try:
            response = self.table.scan()
            items = response.get("Items", [])
            return sorted(items, key=lambda t: t.get("created_at", ""), reverse=True)
        except (ClientError, BotoCoreError) as err:
            logger.error("DynamoDB scan failed: %s", err)
            raise AWSIntegrationError(f"DynamoDB query failed: {err}")

    def get_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.table.get_item(Key={"task_id": task_id})
            return response.get("Item")
        except (ClientError, BotoCoreError) as err:
            logger.error("DynamoDB get_item failed: %s", err)
            raise AWSIntegrationError(f"DynamoDB lookup failed: {err}")

    def save(self, task_dict: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # DynamoDB requires booleans and non-empty strings
            cleaned_item = {k: v for k, v in task_dict.items() if v is not None}
            self.table.put_item(Item=cleaned_item)
            return task_dict
        except (ClientError, BotoCoreError) as err:
            logger.error("DynamoDB put_item failed: %s", err)
            raise AWSIntegrationError(f"DynamoDB save failed: {err}")

    def delete(self, task_id: str) -> bool:
        try:
            self.table.delete_item(Key={"task_id": task_id})
            return True
        except (ClientError, BotoCoreError) as err:
            logger.error("DynamoDB delete_item failed: %s", err)
            raise AWSIntegrationError(f"DynamoDB delete failed: {err}")


class TaskService:
    """
    High-level Task Service facade orchestrating domain logic and storage adapters.
    """

    def __init__(self):
        # Choose repository adapter based on environment configuration
        if Config.STORAGE_BACKEND == "dynamodb" and Config.DYNAMODB_TABLE_NAME:
            logger.info("Initializing Amazon DynamoDB Task Repository (%s)", Config.DYNAMODB_TABLE_NAME)
            self.repo = DynamoDBTaskRepository(Config.DYNAMODB_TABLE_NAME, Config.AWS_REGION)
        else:
            logger.info("Initializing Local JSON Task Repository (%s)", Config.LOCAL_STORAGE_PATH)
            self.repo = LocalJSONTaskRepository(Config.LOCAL_STORAGE_PATH)

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        return self.repo.get_all()

    def get_task(self, task_id: str) -> Dict[str, Any]:
        task = self.repo.get_by_id(task_id)
        if not task:
            raise NotFoundError(f"Task with ID '{task_id}' not found")
        return task

    def create_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        task = Task.from_dict(payload)
        saved = self.repo.save(task.to_dict())
        logger.info("Task created successfully: %s ('%s')", task.task_id, task.title)
        return saved

    def update_task(self, task_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        existing = self.get_task(task_id)
        task = Task.from_dict(existing)
        task.update(fields)
        saved = self.repo.save(task.to_dict())
        logger.info("Task updated successfully: %s", task_id)
        return saved

    def toggle_complete(self, task_id: str) -> Dict[str, Any]:
        existing = self.get_task(task_id)
        task = Task.from_dict(existing)
        if task.status == "completed":
            task.mark_pending()
        else:
            task.mark_completed()
        saved = self.repo.save(task.to_dict())
        logger.info("Task completion toggled: %s -> %s", task_id, task.status)
        return saved

    def delete_task(self, task_id: str) -> bool:
        # Check existence first
        self.get_task(task_id)
        success = self.repo.delete(task_id)
        logger.info("Task deleted: %s (success=%s)", task_id, success)
        return success


# Singleton instance
task_service = TaskService()
