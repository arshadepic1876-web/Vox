# COLLEGE PROJECT REPORT

## PROJECT TITLE:
### AI Voice-to-Text Task Manager using AWS (VOX)

---

### 1. ABSTRACT
In today’s fast-paced digital ecosystem, effective time and task management are fundamental to academic and professional productivity. However, conventional task management applications introduce significant operational friction by forcing users to manually type titles, navigate multiple calendar pickers, configure dropdown priority menus, and select categorization tags. This friction frequently results in abandoned to-do lists and delayed deadlines.

This project, titled **"AI Voice-to-Text Task Manager using AWS" (VOX)**, presents an intelligent, cloud-integrated productivity web application that eliminates manual entry barriers through automated speech recognition (ASR) and natural language processing (NLP). The user speaks naturally in conversational English (e.g., *"Remind me to submit my Python assignment tomorrow at 5 PM. It is very important."*). The client application captures high-fidelity audio via the modern browser `MediaRecorder` API and transmits it to a decoupled Python Flask backend. The backend temporarily stores the recording in **Amazon S3**, invokes **Amazon Transcribe** for automated speech-to-text conversion, immediately purges transient audio to eliminate storage costs and preserve privacy, and parses the extracted text using an intelligent NLP engine. 

The NLP engine automatically extracts structured attributes: task title, relative calendar date normalization, time resolution, priority tier (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), urgency flag, and domain category (`College`, `Work`, `Personal`, etc.). To prevent algorithmic hallucination, the system implements a **Human-in-the-Loop Confirmation Preview** allowing users to inspect and refine parameters before writing to an abstracted storage layer powered by **Amazon DynamoDB** (with local JSON fallback). The responsive frontend provides dynamic statistics, multi-tier sorting, real-time search, and filter pills. The system demonstrates enterprise cloud engineering practices, including IAM least-privilege role-based access control, zero client-side credential exposure, and robust production testing.

---

### 2. INTRODUCTION
Human speech is the most natural, expressive, and rapid form of human communication. While an average individual types approximately 40 words per minute on a computer keyboard and fewer on a mobile touch screen, normal conversational speech flows at 130 to 160 words per minute. Despite this efficiency advantage, speech remains underutilized in structured information systems.

Most existing speech applications function merely as raw dictation tools or voice memo recorders. While these tools record audio or output unstructured paragraphs of text, they fail to extract semantic relationships. A voice note containing a deadline does not automatically create a calendar item, set priority alerts, or categorize responsibilities. 

The **VOX AI Voice-to-Text Task Manager** bridges this fundamental divide by coupling AWS cloud-scale speech recognition with natural language intent understanding.

---

### 3. PROBLEM STATEMENT
Traditional to-do and productivity applications suffer from three critical bottlenecks:
1. **Input Latency and Cognitive Friction**: Creating a detailed task manually requires 6 to 10 distinct UI interactions (typing text, selecting date pickers, opening dropdowns, clicking checkboxes).
2. **Lack of Semantic Understanding in Voice Memos**: Existing voice recorders store unstructured audio or plain transcripts without extracting actionable parameters (who, what, when, priority).
3. **Security Vulnerabilities in Novice Cloud Implementations**: Many academic cloud projects inadvertently expose AWS credentials directly inside client JavaScript files or leave cloud resources unmonitored, resulting in security breaches and unexpected financial costs.

---

### 4. EXISTING SYSTEM
Existing systems can be categorized into:
* **Conventional Task Applications (e.g., Todoist, Google Tasks, Apple Reminders)**: Excellent visual task organization, but primarily rely on manual keyboard input and extensive form clicking.
* **Basic Speech Dictation Tools (e.g., Google Keep Voice Memos, Voice Recorder apps)**: Capable of converting voice to raw text, but incapable of understanding intent, extracting normalized dates, calculating urgency, or generating structured JSON entities.

#### Limitations of Existing Systems:
* Inefficient task creation workflow while commuting or multitasking.
* No automatic date/time normalization from relative phrases (*"day after tomorrow"*, *"next Friday at 4 PM"*).
* No differentiation between task **Priority** (importance of task) and **Urgency** (time sensitivity of task).

---

### 5. PROPOSED SYSTEM
The proposed system, **VOX**, provides an end-to-end cloud pipeline that converts conversational speech into fully structured, editable, and trackable tasks:
* **Single-Tap Voice Capture**: Captures speech directly in the browser with real-time audio wave feedback and recording timers.
* **AWS Speech Recognition Pipeline**: Utilizes Amazon S3 and Amazon Transcribe for high-accuracy batch speech-to-text conversion.
* **Intelligent NLP Attribute Extraction**: Employs context-aware natural language parsing to resolve relative dates, normalize times, classify categories, and identify urgency.
* **Human-in-the-Loop Verification**: Displays a "Task Detected" preview card allowing the user to confirm or edit details before database commit.
* **Comprehensive Task Management**: Provides full CRUD capabilities, dynamic KPI analytics, multi-criteria sorting, and instant search.

---

### 6. OBJECTIVES
1. To develop a decoupled, production-grade web application architecture featuring an HTML5/CSS3/Vanilla JS frontend and a Python Flask REST API backend.
2. To integrate Amazon S3 for transient audio staging with immediate post-processing cleanup to ensure zero permanent storage fees.
3. To leverage Amazon Transcribe for automatic speech recognition.
4. To build an intelligent NLP task parser capable of resolving relative calendar dates based on configured timezones (`Asia/Kolkata`).
5. To implement Amazon DynamoDB for scalable, serverless NoSQL persistence.
6. To enforce strict cloud security standards using IAM instance profiles and zero client-side credential leakage.

---

### 7. TECHNOLOGIES USED

#### Frontend:
* **HTML5**: Semantic document structure and accessible forms.
* **CSS3**: Custom design tokens, Flexbox, CSS Grid, animations, and responsive media queries.
* **Vanilla JavaScript (ES6+)**: DOM manipulation, event dispatching, and asynchronous requests.
* **MediaRecorder API**: Native browser audio capture and binary Blob formatting.
* **Fetch API**: Centralized RESTful HTTP communication.

#### Backend:
* **Python 3.10+**: Core programming language.
* **Flask**: Lightweight microframework for routing and RESTful request handling.
* **Flask-CORS**: Cross-Origin Resource Sharing control.
* **python-dotenv**: Environment configuration isolation.
* **boto3**: Official AWS SDK for Python.
* **Gunicorn**: Production WSGI HTTP server.

#### AWS Cloud Infrastructure:
* **Amazon S3**: Private object storage for temporary audio buffering.
* **Amazon Transcribe**: Automatic Speech Recognition (ASR) service.
* **Amazon DynamoDB**: Serverless, low-latency NoSQL database.
* **Amazon EC2**: Virtual cloud server running Ubuntu Linux.
* **AWS IAM**: Role-based access control and least-privilege security.

---

### 8. SYSTEM REQUIREMENTS

#### Hardware Requirements:
* **Processor**: 64-bit Dual Core CPU (Intel Core i3 / AMD Ryzen 3 or higher).
* **RAM**: 4 GB minimum (8 GB recommended).
* **Storage**: 500 MB available local disk space.
* **Microphone**: Integrated or external microphone (16 kHz minimum sampling rate).

#### Software Requirements:
* **Operating System**: Windows 10/11, macOS, or Ubuntu Linux 22.04+.
* **Browser**: Google Chrome 90+, Mozilla Firefox 88+, or Microsoft Edge 90+.
* **Runtime**: Python 3.10 or higher.
* **Cloud Account**: AWS Account (Free Tier eligible).

---

### 9. FUNCTIONAL REQUIREMENTS
* **FR-01 (Audio Recording)**: The system must capture microphone audio upon user initiation and display live recording time.
* **FR-02 (Input Validation)**: The system must reject empty recordings, recordings shorter than 1 second, and files larger than 10 MB.
* **FR-03 (Speech Transcription)**: The backend must process audio via Amazon Transcribe and produce accurate English text.
* **FR-04 (Intent Extraction)**: The system must extract Title, Due Date, Due Time, Priority, Urgency, Category, and Duration from transcripts.
* **FR-05 (Confirmation Preview)**: The system must display a preview modal of extracted data prior to database commit.
* **FR-06 (Manual Task Creation)**: Users must be able to create tasks manually through a structured form.
* **FR-07 (Task Operations)**: Users must be able to view, edit, complete, reopen, and delete tasks.
* **FR-08 (Filtering & Search)**: Users must be able to search tasks by keyword and filter by status, urgency, and priority.

---

### 10. NON-FUNCTIONAL REQUIREMENTS
* **NFR-01 (Security)**: Zero cloud credentials in client code; private S3 buckets; sanitized error responses.
* **NFR-02 (Performance)**: Audio upload and parsing pipeline must complete in under 5 seconds under normal network conditions.
* **NFR-03 (Reliability)**: The backend must gracefully fall back to local rule-based NLP if external AI APIs are unreachable.
* **NFR-04 (Responsiveness)**: The web UI must fluidly adapt to mobile (375px), tablet (768px), and desktop (1200px+) viewports.
* **NFR-05 (Cost Efficiency)**: Transient audio files must be automatically purged to eliminate AWS S3 storage costs.

---

### 11. SYSTEM ARCHITECTURE
The system employs a **3-Tier Decoupled Client-Server Cloud Architecture**:
1. **Presentation Tier (Browser)**: Executes purely on the client device. Captures audio via `MediaRecorder` and renders task cards via Vanilla JS.
2. **Application Tier (Flask / EC2)**: Orchestrates business logic, validates payloads, manages AWS SDK clients, and hosts the NLP engine.
3. **Data Tier (S3 & DynamoDB)**: Stores temporary binary recordings in S3 and permanent structured task entities in DynamoDB.

---

### 12. DATA FLOW
```
[User Speech] ──► Browser MediaRecorder ──► Multipart POST ──► Flask Route
                                                                     │
       ┌─────────────────────────────────────────────────────────────┘
       ▼
S3 Upload (Temporary) ──► Amazon Transcribe ──► Raw Transcript ──► S3 Delete
                                                                     │
       ┌─────────────────────────────────────────────────────────────┘
       ▼
AI / NLP Engine (Date/Time Resolution, Priority, Urgency)
       │
       ▼
JSON Candidate ──► Human Preview Modal ──► User Confirms ──► DynamoDB Store
```

---

### 13. SEQUENCE DIAGRAM
Refer to [`docs/architecture.md`](file:///c:/Users/Arshad%20Reza/Downloads/VOX/docs/architecture.md) for the complete sequence diagram detailing step-by-step interactions between User, Browser, Flask, S3, Transcribe, and DynamoDB.

---

### 14. MODULES
1. **Voice Capture Module (`recorder.js`)**: Manages microphone streams, timers, sound wave animations, and Blob packaging.
2. **Dashboard Controller (`dashboard.js`)**: Manages live statistics, filter pills, search bar, and confirmation modals.
3. **REST API Client (`api.js`)**: Provides a unified HTTP client for backend communication.
4. **Validation & Security Layer (`validation.py`, `errors.py`)**: Sanitizes inputs and formats consistent JSON error responses.
5. **AWS S3 Service (`s3_service.py`)**: Handles audio buffering and transient file deletion.
6. **Amazon Transcribe Service (`transcribe_service.py`)**: Manages ASR batch jobs and transcript retrieval.
7. **Task Parser Engine (`task_parser.py`)**: Extracts structured entities using timezone-aware NLP.
8. **Task Repository Service (`task_service.py`)**: Implements the Abstracted Repository Pattern supporting both Local JSON and Amazon DynamoDB.

---

### 15. WORKING METHODOLOGY
The system operates on an event-driven request-response model:
1. **Audio Ingestion**: Spoken words are digitized into an Opus-compressed `.webm` stream.
2. **Cloud Speech Processing**: Audio is buffered in a private S3 bucket and processed via Amazon Transcribe.
3. **Temporal & Semantic Normalization**: The text is evaluated against a reference timestamp in the configured timezone (`Asia/Kolkata`) to normalize relative dates (*"tomorrow"* &rarr; exact calendar date).
4. **User Verification**: Extracted data is presented to the user in a preview modal to verify correctness.
5. **Storage & Dashboard Refresh**: Confirmed tasks are persisted to DynamoDB, and the dashboard metrics update dynamically.

---

### 16. AWS ARCHITECTURE & SECURITY DESIGN
* **IAM Instance Profiles**: In production EC2 deployment, the backend acquires permissions via an IAM Role (`VOX-EC2-BackendRole`) rather than hardcoded access keys on disk.
* **Private Bucket Access**: Amazon S3 has "Block all public access" enabled.
* **Transient Audio Deletion**: Audio files in S3 are deleted immediately after transcription completes, supplemented by an S3 Lifecycle Rule that purges files after 24 hours.

---

### 17. DATABASE DESIGN
The application utilizes an Abstracted Repository Pattern supporting two interchangeable backends:
1. **Local JSON Repository (`data/tasks.json`)**: Enables offline local development without AWS credentials.
2. **Amazon DynamoDB (`VoxTasks`)**: Serverless NoSQL table indexed by partition key `task_id` (UUID v4). Attributes include `title`, `description`, `due_date`, `due_time`, `priority`, `urgent`, `category`, `status`, `created_at`, and `updated_at`.

---

### 18. API DESIGN
The backend exposes 8 RESTful endpoints adhering to standard HTTP methods and status codes:
* `GET /api/health` (200 OK)
* `POST /api/transcribe` (200 OK, 400 Bad Request, 413 Payload Too Large, 422 Unprocessable)
* `GET /api/tasks` (200 OK)
* `POST /api/tasks` (201 Created)
* `GET /api/tasks/<id>` (200 OK, 404 Not Found)
* `PUT /api/tasks/<id>` (200 OK, 404 Not Found)
* `PATCH /api/tasks/<id>/complete` (200 OK, 404 Not Found)
* `DELETE /api/tasks/<id>` (200 OK, 404 Not Found)
* `POST /api/tasks/parse` (200 OK)

---

### 19. IMPLEMENTATION
* Decoupled frontend using clean Vanilla JavaScript ES6 classes and modular CSS.
* Python Flask application factory pattern (`create_app()`) with blueprint routing.
* Dual-engine NLP parser featuring LLM structured output and an offline regex/heuristics engine.

---

### 20. TESTING
The application was verified through an automated 8-test unit test suite (`tests/test_api.py`) and a comprehensive 25-point end-to-end test matrix (`docs/testing.md`). Tests verified microphone error handling, payload size limits, relative date normalization, priority classification, and full CRUD cycles.

---

### 21. ADVANTAGES
1. **Rapid Task Creation**: Creates a comprehensive task with deadlines and priorities in 3 seconds of speech.
2. **Cost-Effective Architecture**: Zero persistent S3 storage fees and DynamoDB permanent Free Tier eligibility.
3. **No Framework Bloat**: Vanilla JS architecture ensures instant page loading without large npm bundles.
4. **Cloud-Native & Secure**: Adheres to AWS security best practices using IAM roles.

---

### 22. LIMITATIONS
1. **Batch Transcription Latency**: Uses Amazon Transcribe batch mode, which introduces a 2–4 second turnaround.
2. **Acoustic Noise Sensitivity**: Heavy background noise can degrade transcription accuracy.
3. **Single-User Architecture**: Multi-tenancy and personalized user authentication are reserved for future phases.

---

### 23. FUTURE SCOPE
1. **Real-Time Streaming Transcription**: Integrating WebSockets and Amazon Transcribe Streaming for word-by-word real-time display.
2. **Voice Readback with Amazon Polly**: Providing auditory task confirmation via text-to-speech.
3. **User Authentication via Amazon Cognito**: Multi-user account management and private task isolation.
4. **Automated Reminders via Amazon SNS**: SMS and email notifications for upcoming deadlines.

---

### 24. CONCLUSION
The **AI Voice-to-Text Task Manager using AWS (VOX)** demonstrates how cloud speech recognition and natural language parsing can be combined into a modern productivity application. By strictly separating frontend and backend tiers, enforcing AWS least-privilege security, and providing a human-in-the-loop preview step, VOX delivers a robust, accessible, and production-ready solution suitable for academic submission and real-world deployment.

---

### 25. REFERENCES
1. Amazon Web Services. *Amazon Transcribe Developer Guide*. AWS Documentation, 2024.
2. Amazon Web Services. *Amazon DynamoDB Developer Guide*. AWS Documentation, 2024.
3. MDN Web Docs. *MediaStream Recording API*. Mozilla Developer Network, 2024.
4. Grinberg, Miguel. *Flask Web Development: Developing Web Applications with Python*. O'Reilly Media, 2018.
5. Fielding, Roy Thomas. *Architectural Styles and the Design of Network-based Software Architectures*. PhD Dissertation, University of California, Irvine, 2000.
