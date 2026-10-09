# REST API Specification

Comprehensive documentation for all REST API endpoints provided by the VOX backend.

**Base URL**: `http://localhost:5000/api` (Local) or `https://<your-ec2-ip>/api` (Production)

---

## 1. System Health

### `GET /api/health`
Checks operational vitality of the API and active configuration.

* **Response (200 OK)**:
```json
{
  "success": true,
  "message": "VOX AI Task Manager API is healthy and operational",
  "data": {
    "status": "online",
    "timestamp": "2026-10-09T00:25:00+05:30",
    "config": {
      "port": 5000,
      "environment": "development",
      "timezone": "Asia/Kolkata",
      "storage_backend": "local",
      "aws_region": "ap-south-1",
      "aws_s3_configured": false,
      "ai_parser_provider": "rule_based"
    }
  }
}
```

---

## 2. Speech-to-Text & Transcription

### `POST /api/transcribe`
Ingests an audio recording, executes speech recognition via Amazon Transcribe, and parses structured task attributes using the AI task parser.

* **Content-Type**: `multipart/form-data`
* **Form Parameters**:
  * `audio` *(file, required)*: Binary audio file (`audio/webm`, `audio/wav`, `audio/ogg`). Max 10 MB.
  * `language` *(string, optional)*: Language code, e.g., `en-US`, `en-IN` (Default: `en-US`).

* **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Speech transcribed and task parameters extracted successfully",
  "data": {
    "title": "Submit Python assignment",
    "description": "Submit Python assignment tomorrow at 5 PM. It is very important.",
    "due_date": "2026-10-10",
    "due_time": "17:00",
    "priority": "HIGH",
    "urgent": false,
    "category": "College",
    "status": "pending",
    "estimated_duration_minutes": null,
    "raw_transcription": "Submit Python assignment tomorrow at 5 PM. It is very important."
  }
}
```

* **Error Responses**:
  * `400 Bad Request`: Missing `audio` file in request, or empty file.
  * `413 Payload Too Large`: Audio file exceeds `MAX_AUDIO_SIZE_MB` limit.
  * `422 Unprocessable Entity`: Corrupted audio stream or transcription failure.

---

## 3. Task Management (CRUD)

### `GET /api/tasks`
Retrieve all tasks.

* **Response (200 OK)**:
```json
{
  "success": true,
  "count": 1,
  "data": [
    {
      "task_id": "c8e42f1b-31a9-467f-94ad-73a7c64593e1",
      "title": "Submit Python assignment",
      "description": "Due on campus portal",
      "due_date": "2026-10-10",
      "due_time": "17:00",
      "priority": "HIGH",
      "urgent": true,
      "category": "College",
      "status": "pending",
      "estimated_duration_minutes": 60,
      "created_at": "2026-10-09T00:25:00+05:30",
      "updated_at": "2026-10-09T00:25:00+05:30"
    }
  ]
}
```

---

### `POST /api/tasks`
Create a new structured task.

* **Content-Type**: `application/json`
* **Request Body**:
```json
{
  "title": "Finish Database Schema Design",
  "description": "Design 3NF relational tables",
  "due_date": "2026-10-12",
  "due_time": "14:00",
  "priority": "CRITICAL",
  "urgent": true,
  "category": "College"
}
```

* **Response (201 Created)**:
```json
{
  "success": true,
  "message": "Task created successfully",
  "data": {
    "task_id": "e93f12ab-...",
    "title": "Finish Database Schema Design",
    "status": "pending",
    "created_at": "..."
  }
}
```

---

### `GET /api/tasks/<task_id>`
Fetch a single task by its unique ID.

* **Response (200 OK)**: Task item object.
* **Response (404 Not Found)**: `{"success": false, "message": "Task with ID '...' not found"}`

---

### `PUT /api/tasks/<task_id>`
Update any field of an existing task.

* **Request Body**: JSON containing fields to modify (`title`, `due_date`, `priority`, etc.).
* **Response (200 OK)**: Returns updated task object.

---

### `PATCH /api/tasks/<task_id>/complete`
Toggles task status between `pending` and `completed`.

* **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Task marked as completed",
  "data": { ... }
}
```

---

### `DELETE /api/tasks/<task_id>`
Permanently deletes a task.

* **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Task deleted successfully"
}
```

---

### `POST /api/tasks/parse`
Parses raw text directly into structured task JSON (useful for testing or fallback text input).

* **Content-Type**: `application/json`
* **Request Body**:
```json
{
  "text": "Call doctor tomorrow at 11 AM. It is urgent."
}
```
* **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Task parsed successfully from text input",
  "data": {
    "title": "Call doctor",
    "due_date": "2026-10-10",
    "due_time": "11:00",
    "priority": "MEDIUM",
    "urgent": true,
    "category": "Health",
    "status": "pending"
  }
}
```
