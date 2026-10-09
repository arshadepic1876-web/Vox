import logging
from flask import Blueprint, request, jsonify
from utils.validation import validate_task_payload
from utils.errors import ValidationError
from services.task_service import task_service
from services.task_parser import task_parser_service

logger = logging.getLogger(__name__)

tasks_bp = Blueprint("tasks", __name__, url_prefix="/api")


@tasks_bp.route("/tasks", methods=["GET"])
def get_all_tasks():
    """
    GET /api/tasks
    Retrieve all tasks sorted by creation date.
    """
    tasks = task_service.get_all_tasks()
    return jsonify({
        "success": True,
        "count": len(tasks),
        "data": tasks,
    }), 200


@tasks_bp.route("/tasks/<task_id>", methods=["GET"])
def get_task_by_id(task_id: str):
    """
    GET /api/tasks/<task_id>
    Retrieve a specific task by its UUID.
    """
    task = task_service.get_task(task_id)
    return jsonify({
        "success": True,
        "data": task,
    }), 200


@tasks_bp.route("/tasks", methods=["POST"])
def create_task():
    """
    POST /api/tasks
    Create a new structured task (manual creation or confirmed preview).
    """
    payload = request.get_json(silent=True)
    if not payload:
        raise ValidationError("Request body must be a valid JSON object")

    cleaned = validate_task_payload(payload, is_update=False)
    created = task_service.create_task(cleaned)

    return jsonify({
        "success": True,
        "message": "Task created successfully",
        "data": created,
    }), 201


@tasks_bp.route("/tasks/<task_id>", methods=["PUT"])
def update_task(task_id: str):
    """
    PUT /api/tasks/<task_id>
    Update an existing task's attributes.
    """
    payload = request.get_json(silent=True)
    if not payload:
        raise ValidationError("Request body must be a valid JSON object")

    cleaned = validate_task_payload(payload, is_update=True)
    updated = task_service.update_task(task_id, cleaned)

    return jsonify({
        "success": True,
        "message": "Task updated successfully",
        "data": updated,
    }), 200


@tasks_bp.route("/tasks/<task_id>/complete", methods=["PATCH"])
def toggle_task_complete(task_id: str):
    """
    PATCH /api/tasks/<task_id>/complete
    Toggle completion status between 'completed' and 'pending'.
    """
    toggled = task_service.toggle_complete(task_id)
    return jsonify({
        "success": True,
        "message": f"Task marked as {toggled['status']}",
        "data": toggled,
    }), 200


@tasks_bp.route("/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id: str):
    """
    DELETE /api/tasks/<task_id>
    Permanently delete a task.
    """
    task_service.delete_task(task_id)
    return jsonify({
        "success": True,
        "message": "Task deleted successfully",
    }), 200


@tasks_bp.route("/tasks/parse", methods=["POST"])
def parse_text_task():
    """
    POST /api/tasks/parse
    Utility endpoint: Parse raw text into structured task JSON
    without uploading an audio recording.
    """
    payload = request.get_json(silent=True)
    if not payload or "text" not in payload:
        raise ValidationError("JSON body must include a 'text' string")

    raw_text = payload.get("text", "").strip()
    if not raw_text:
        raise ValidationError("'text' field cannot be blank")

    parsed = task_parser_service.parse_transcription(raw_text)
    return jsonify({
        "success": True,
        "message": "Task parsed successfully from text input",
        "data": parsed,
    }), 200
