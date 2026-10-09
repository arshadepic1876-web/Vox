# College Viva Voce & Defense Q&A Guide

Essential questions, answers, and technical defense arguments for your college project viva.

---

### Q1: Why did you separate the Frontend and Backend completely?
**Answer**: 
"In enterprise software architecture, decoupling presentation from business logic is essential. The browser frontend is a public, untrusted environment. If we made AWS calls directly from JavaScript, our AWS access keys would be visible in browser Developer Tools (F12) to anyone inspecting the page. By placing all AWS operations behind our Python Flask REST API, our cloud credentials remain securely on the server."

---

### Q2: Why does the system upload audio to Amazon S3 before Amazon Transcribe?
**Answer**: 
"Amazon Transcribe batch speech recognition requires an input audio source stored in an Amazon S3 bucket (`s3://...`). Therefore, our backend buffers the audio file in a private S3 bucket, initiates the transcription job, retrieves the resulting text transcript, and then immediately deletes the audio file from S3 so that no unnecessary storage charges are incurred."

---

### Q3: How do you handle storage costs in Amazon S3 so you don't get billed?
**Answer**: 
"We employ a two-layer cost optimization strategy:
1. **Immediate programmatic deletion**: In `s3_service.py`, as soon as Transcribe returns the text, we call `s3.delete_object()`.
2. **S3 Lifecycle Rule safeguard**: In our S3 bucket configuration, we added a rule that automatically expires and deletes all objects after 1 day. This guarantees that even if the server crashes unexpectedly mid-request, transient audio never remains permanently."

---

### Q4: How does your NLP engine resolve relative dates like "tomorrow" or "next Friday"?
**Answer**: 
"Relative dates cannot be resolved without a reference point and a specific timezone. Our Task Parser determines the current datetime in the configured timezone (`Asia/Kolkata` from `.env`). When the user says *'tomorrow'*, the system calculates `now + timedelta(days=1)`. For days of the week like *'next Friday'*, it calculates the difference between today's weekday index and Friday's index, mapping it to an exact ISO calendar date (`YYYY-MM-DD`)."

---

### Q5: What is the difference between Priority and Urgency in your application?
**Answer**: 
"Priority and Urgency are distinct dimensions of productivity:
* **Priority** represents the **importance/impact** of the task (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
* **Urgency** represents the **time sensitivity** of the task (`true` or `false`).
For example, submitting an assignment due in 1 hour is both Urgent and High Priority, whereas scheduling an annual health checkup is High Priority but Not Urgent."

---

### Q6: Why did you choose Amazon DynamoDB instead of a traditional relational database (MySQL)?
**Answer**: 
"DynamoDB was chosen for three primary reasons:
1. **Serverless & Zero Maintenance**: No database server instances to patch or manage.
2. **Document Model**: Our tasks are represented as structured JSON entities, which map directly to DynamoDB items without requiring relational migrations.
3. **AWS Free Tier Advantage**: DynamoDB provides 25 GB of permanent free storage and 25 capacity units under AWS Always Free, making it ideal for student and production workloads."

---

### Q7: Why did you use an IAM Instance Role on EC2 instead of storing access keys?
**Answer**: 
"Hardcoding `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in server files creates a significant security vulnerability if code or backups are leaked. With an **IAM Instance Profile**, AWS automatically generates and rotates temporary security tokens that `boto3` transparently fetches from the EC2 instance metadata service (`169.254.169.254`). There are zero static secrets on the server disk."

---

### Q8: Why did you implement a 'Task Detected' Preview modal instead of saving the task directly?
**Answer**: 
"This embodies the **Human-in-the-Loop** design principle. Speech recognition and AI parsing can occasionally mishear words or misinterpret acoustic nuances. By showing a preview card with `[Edit Details]` and `[Create Task]`, the user has full control to verify and adjust the task before it is committed to the database."

---

### Q9: Why did you use Vanilla JavaScript instead of React?
**Answer**: 
"Vanilla JavaScript eliminated build-tool complexity (like Webpack, Node.js runtime, and massive `node_modules` folders) while achieving near-instant page load times. It also demonstrates a strong mastery of core web fundamentals: semantic HTML5, CSS custom properties, and native asynchronous APIs like `MediaRecorder` and `Fetch`."

---

### Q10: How does your system handle offline or local development if AWS is not yet configured?
**Answer**: 
"We built an **Abstracted Repository Pattern** and a **Dual-Mode Parser**. If AWS credentials are not in `.env`, the system smoothly runs in offline development mode: tasks are stored in `backend/data/tasks.json` and parsed using our deterministic regex/heuristics engine. The entire application runs out-of-the-box on any computer without requiring paid cloud accounts."
