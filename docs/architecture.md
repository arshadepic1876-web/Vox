# System Architecture & Technical Diagrams

Comprehensive architectural documentation and Mermaid diagrams for **VOX - AI Voice-to-Text Task Manager using AWS**.

---

## 1. System Architecture Diagram

```mermaid
flowchart TD
    subgraph Client["Frontend Client (Browser)"]
        UI["User Dashboard (HTML5 / CSS3)"]
        Rec["Recorder Module (MediaRecorder API)"]
        API_Client["API Client (Fetch API)"]
        PreviewModal["Task Preview & Confirmation Modal"]
    end

    subgraph Server["Backend Server (Python Flask / Gunicorn)"]
        Router["Flask REST API Router"]
        Val["Audio & Payload Validator"]
        S3_Svc["S3 Storage Service"]
        Trans_Svc["Amazon Transcribe Service"]
        Parser_Svc["AI Task Understanding Engine"]
        Task_Svc["Task Repository Service"]
    end

    subgraph AWS["AWS Cloud Infrastructure"]
        S3[("Amazon S3 Bucket (Private / Transient Audio)")]
        Transcribe["Amazon Transcribe (Speech-to-Text)"]
        DynamoDB[("Amazon DynamoDB (Task Store)")]
    end

    UI -->|1. Tap to record| Rec
    Rec -->|2. Raw Audio Blob| API_Client
    API_Client -->|3. POST /api/transcribe| Router
    Router --> Val
    Val -->|4. Validated Audio| S3_Svc
    S3_Svc -->|5. Upload Object| S3
    S3_Svc -->|6. S3 URI| Trans_Svc
    Trans_Svc -->|7. Start Job & Fetch Result| Transcribe
    Transcribe -->|8. Raw Transcript Text| Trans_Svc
    Trans_Svc -->|9. Delete Temp Audio| S3
    Trans_Svc -->|10. Text Transcript| Parser_Svc
    Parser_Svc -->|11. Extracted JSON| Router
    Router -->|12. Return Candidate JSON| API_Client
    API_Client -->|13. Display Preview| PreviewModal
    PreviewModal -->|14. User Confirms / Edits| API_Client
    API_Client -->|15. POST /api/tasks| Router
    Router --> Task_Svc
    Task_Svc -->|16. PutItem| DynamoDB
    DynamoDB -->|17. Saved Task| Task_Svc
    Task_Svc -->|18. 201 Created| API_Client
    API_Client -->|19. Render Task Card| UI
```

---

## 2. Voice-to-Task Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor User as User
    participant Browser as Browser (MediaRecorder)
    participant Flask as Flask REST API
    participant S3 as Amazon S3
    participant Transcribe as Amazon Transcribe
    participant AI as Task Parser (AI/NLP)
    participant DB as DynamoDB / Local Storage

    User->>Browser: Speaks "Submit OS assignment tomorrow at 4 PM. It is urgent."
    Browser->>Browser: Packages Opus/WebM Blob
    Browser->>Flask: POST /api/transcribe (FormData with audio)
    Flask->>Flask: Validate file size (<10MB) & MIME type
    Flask->>S3: Upload transient audio (recordings/{uuid}.webm)
    Flask->>Transcribe: StartTranscriptionJob(s3_uri)
    Transcribe-->>Flask: Completed Transcript ("Submit OS assignment...")
    Flask->>S3: DeleteObject (cleanup audio)
    Flask->>AI: parse_transcription(transcript, timezone)
    AI-->>Flask: Structured Task JSON (Title, Date, Time, Priority, Urgency)
    Flask-->>Browser: 200 OK (Candidate Task Data)
    Browser->>User: Displays "TASK DETECTED" Preview Modal
    User->>Browser: Clicks [Create Task]
    Browser->>Flask: POST /api/tasks (Confirmed Task JSON)
    Flask->>DB: Save Task
    DB-->>Flask: Saved Confirmation
    Flask-->>Browser: 201 Created
    Browser->>User: Renders Task on Dashboard & Updates KPI Stats
```

---

## 3. Deployment Architecture Diagram

```mermaid
flowchart LR
    Internet((Internet / Users)) -->|Port 443 / HTTPS| Nginx["Nginx Web Server"]
    Nginx -->|Reverse Proxy :5000| Gunicorn["Gunicorn WSGI Process Manager"]
    Gunicorn --> Worker1["Flask Worker 1"]
    Gunicorn --> Worker2["Flask Worker 2"]
    Gunicorn --> Worker3["Flask Worker 3"]
    
    subgraph AWS_Cloud["AWS Region: ap-south-1 (Mumbai)"]
        subgraph EC2["Amazon EC2 (t2.micro Ubuntu)"]
            Nginx
            Gunicorn
            Worker1
            Worker2
            Worker3
        end
        
        IAM["IAM Instance Role: VOX-EC2-BackendRole"] -.->|Zero Credentials on Disk| EC2
        Worker1 --> S3[("Amazon S3 Bucket")]
        Worker1 --> Transcribe["Amazon Transcribe"]
        Worker1 --> DynamoDB[("Amazon DynamoDB")]
    end
```

---

## 4. Task Lifecycle State Machine

```mermaid
stateDiagram-v2
    [*] --> VoiceRecording: User Taps Mic
    VoiceRecording --> Transcribing: Audio Sent to API
    Transcribing --> TaskPreview: AI Extracts Parameters
    TaskPreview --> InProgress: User Confirms / Adds
    TaskPreview --> Editing: User Clicks [Edit Details]
    Editing --> InProgress: User Saves Edits
    
    InProgress --> Completed: User Marks Complete
    Completed --> InProgress: User Reopens Task
    InProgress --> Deleted: User Confirms Delete
    Completed --> Deleted: User Confirms Delete
    Deleted --> [*]
```
