import io
import os
import sys
import unittest

# Ensure backend folder is on sys.path regardless of execution CWD
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from services.task_parser import task_parser_service


class VoxAPITestCase(unittest.TestCase):
    """
    Comprehensive Test Suite for VOX AI Voice Task Manager.
    Covers Health, Task CRUD, Parsing, Audio Validation, and Error Handling.
    """

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_01_health_check(self):
        """Verify GET /api/health returns 200 and online status."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["data"]["status"], "online")

    def test_02_text_task_parsing_college(self):
        """Verify task parser extracts College category, High priority, 17:00 time."""
        sample_text = "Remind me to submit my Python assignment tomorrow at 5 PM. It is very important."
        parsed = task_parser_service.parse_transcription(sample_text)

        self.assertIn("Python assignment", parsed["title"])
        self.assertEqual(parsed["priority"], "HIGH")
        self.assertEqual(parsed["due_time"], "17:00")
        self.assertEqual(parsed["category"], "College")
        self.assertEqual(parsed["status"], "pending")

    def test_03_text_task_parsing_urgent_work(self):
        """Verify urgency and critical priority detection."""
        sample_text = "Urgently finish the presentation for client meeting before 10 AM. This is critical."
        parsed = task_parser_service.parse_transcription(sample_text)

        self.assertTrue(parsed["urgent"])
        self.assertEqual(parsed["priority"], "CRITICAL")
        self.assertEqual(parsed["due_time"], "10:00")
        self.assertIn(parsed["category"], ["Work", "Meeting"])

    def test_04_create_and_read_task(self):
        """Verify POST /api/tasks and GET /api/tasks."""
        payload = {
            "title": "Study Operating Systems",
            "description": "Read chapters 3 and 4",
            "priority": "HIGH",
            "urgent": True,
            "category": "Study",
            "due_date": "2026-10-15",
            "due_time": "14:00",
        }
        create_res = self.client.post("/api/tasks", json=payload)
        self.assertEqual(create_res.status_code, 201)
        created_task = create_res.get_json()["data"]
        self.assertEqual(created_task["title"], "Study Operating Systems")
        task_id = created_task["task_id"]

        # Fetch all
        list_res = self.client.get("/api/tasks")
        self.assertEqual(list_res.status_code, 200)
        tasks = list_res.get_json()["data"]
        self.assertTrue(any(t["task_id"] == task_id for t in tasks))

        # Cleanup
        self.client.delete(f"/api/tasks/{task_id}")

    def test_05_update_task(self):
        """Verify PUT /api/tasks/<id> modifying fields."""
        create_res = self.client.post("/api/tasks", json={"title": "Original Title"})
        task_id = create_res.get_json()["data"]["task_id"]

        update_res = self.client.put(f"/api/tasks/{task_id}", json={
            "title": "Updated Title",
            "priority": "LOW",
        })
        self.assertEqual(update_res.status_code, 200)
        updated = update_res.get_json()["data"]
        self.assertEqual(updated["title"], "Updated Title")
        self.assertEqual(updated["priority"], "LOW")

        # Cleanup
        self.client.delete(f"/api/tasks/{task_id}")

    def test_06_toggle_completion(self):
        """Verify PATCH /api/tasks/<id>/complete toggles pending to completed."""
        create_res = self.client.post("/api/tasks", json={"title": "Toggle Test Task"})
        task_id = create_res.get_json()["data"]["task_id"]

        # Complete
        toggle_res = self.client.patch(f"/api/tasks/{task_id}/complete")
        self.assertEqual(toggle_res.status_code, 200)
        self.assertEqual(toggle_res.get_json()["data"]["status"], "completed")

        # Reopen
        reopen_res = self.client.patch(f"/api/tasks/{task_id}/complete")
        self.assertEqual(reopen_res.status_code, 200)
        self.assertEqual(reopen_res.get_json()["data"]["status"], "pending")

        # Cleanup
        self.client.delete(f"/api/tasks/{task_id}")

    def test_07_validation_empty_title_rejected(self):
        """Verify validation rejects tasks without a title (400 Bad Request)."""
        res = self.client.post("/api/tasks", json={"title": "   "})
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.get_json()["success"])

    def test_08_audio_upload_validation(self):
        """Verify audio upload validation catches empty and missing files."""
        # Missing audio part
        no_file_res = self.client.post("/api/transcribe", data={})
        self.assertEqual(no_file_res.status_code, 400)

        # Empty audio bytes
        empty_res = self.client.post(
            "/api/transcribe",
            data={"audio": (io.BytesIO(b""), "empty.webm")},
        )
        self.assertEqual(empty_res.status_code, 400)

    def test_09_audio_with_genuine_transcript(self):
        """Verify audio upload with real speech transcript extracts accurate task."""
        dummy_audio = b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
        res = self.client.post(
            "/api/transcribe",
            data={
                "audio": (io.BytesIO(dummy_audio), "voice.wav"),
                "transcript": "Buy groceries this evening at 7 PM. High priority.",
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertEqual(data["category"], "Shopping")
        self.assertEqual(data["priority"], "HIGH")
        self.assertEqual(data["due_time"], "19:00")

    def test_10_audio_without_speech_rejected(self):
        """Verify audio without speech and without AWS configured is not spoofed."""
        dummy_audio = b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
        res = self.client.post(
            "/api/transcribe",
            data={"audio": (io.BytesIO(dummy_audio), "silent.wav")},
        )
        # Should cleanly reject rather than inventing a fake task
        self.assertEqual(res.status_code, 422)
        self.assertFalse(res.get_json()["success"])


if __name__ == "__main__":
    unittest.main()
