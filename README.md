# AI Voice-to-Text Task Manager using AWS (VOX)

A professional, cloud-powered productivity web application that captures spoken voice, converts speech to text, extracts structured task parameters (title, date, time, priority, urgency, category) using AI, and organizes tasks in a responsive dashboard.

---

## Architecture Overview

```
User (Voice / Speech)
      │
      ▼
Frontend (HTML5, CSS3, Vanilla JS, MediaRecorder)
      │
      ▼ REST API (FormData / JSON)
Backend (Python 3, Flask, boto3)
      │
      ├── Audio Validation & Transient Upload ──► Amazon S3
      │                                                │
      ├── Speech Recognition Job ───────────────► Amazon Transcribe
      │                                                │
      ├── Task NLP Extraction ◄────────────────────────┘
      │
      ▼ Confirmation / Preview
Database (Amazon DynamoDB / Local JSON Store)
```

---

## Folder Structure

```
VOX/
├── .gitignore               # Root git ignore file
├── README.md                # Project documentation & quickstart
├── frontend/                # Client web application
│   ├── index.html           # Main dashboard & voice recorder
│   ├── tasks.html           # Task management & filter view
│   ├── settings.html        # Configuration & preferences
│   ├── css/                 # Modern responsive styling
│   ├── js/                  # Modular JavaScript components
│   └── assets/              # SVG icons and visual assets
│
├── backend/                 # Python Flask REST API
│   ├── .env.example         # Template configuration
│   ├── .env                 # Local environment secrets (not in git)
│   ├── requirements.txt     # Python dependencies
│   ├── app.py               # Flask application entrypoint
│   ├── config/              # Centralized settings
│   ├── models/              # Domain models (Task)
│   ├── routes/              # API endpoints (health, transcribe, tasks)
│   ├── services/            # S3, Transcribe, AI Parser, Database
│   ├── utils/               # Audio & payload validation, error handlers
│   ├── uploads/             # Temporary staging folder
│   └── data/                # Local data storage
│
└── docs/                    # College report & architecture guides
```

---

## Backend Quickstart

### 1. Prerequisites
- Python 3.10+ installed
- PowerShell or Terminal

### 2. Activate Virtual Environment
```powershell
# Windows
.\backend\.venv\Scripts\Activate.ps1

# Linux / Mac
source backend/.venv/bin/activate
```

### 3. Install Dependencies
```powershell
pip install -r backend/requirements.txt
```

### 4. Run the API Server
```powershell
cd backend
python app.py
```

The API will start at: `http://localhost:5000`

### 5. Verify Server Health
Visit `http://localhost:5000/api/health` in your browser or run:
```powershell
curl http://localhost:5000/api/health
```
