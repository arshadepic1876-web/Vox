# Comprehensive Testing Checklist & Verification Matrix

This document provides a 25-point testing matrix covering audio recording, validation, speech-to-text transcription, AI parsing, and task CRUD lifecycle.

---

## 25-Point Test Matrix

| # | Test Case | Input / Action | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| **1** | Microphone Allowed | Click Mic & select "Allow" | Recording state active, timer starts counting, wave pulses. | Passed | **PASS** |
| **2** | Microphone Denied | Click Mic & select "Block" | Friendly toast: "Microphone permission was denied." | Passed | **PASS** |
| **3** | No Microphone Detected | Disconnect audio hardware | Friendly toast: "No microphone was detected on this device." | Passed | **PASS** |
| **4** | Empty Recording | Click record and stop instantly (<1s) | Rejected: "Recording was too short. Please speak your task." | Passed | **PASS** |
| **5** | Short Recording | 1.5 seconds of silence | System processes without crashing, prompts clear speech. | Passed | **PASS** |
| **6** | Long Recording (>60s) | Record continuously for 60 seconds | Auto-stops at 60s cutoff to protect memory & AWS limits. | Passed | **PASS** |
| **7** | Invalid Audio Format | Upload `.txt` file to `/api/transcribe` | HTTP 400: "Unsupported audio format". | Passed | **PASS** |
| **8** | Audio Exceeding Size Limit | Audio payload > 10 MB | HTTP 400/413: "File exceeds maximum allowed limit". | Passed | **PASS** |
| **9** | Network Offline / Server Down | Stop Flask & interact with frontend | Header pill indicates "Backend Offline"; graceful alert. | Passed | **PASS** |
| **10**| AWS Transcribe Unavailable | AWS keys omitted in `.env` | Safe fallback to offline diagnostic parser; zero crash. | Passed | **PASS** |
| **11**| Transcription Error | Inaudible / corrupted audio stream | HTTP 422: "Speech transcription failed" handled cleanly. | Passed | **PASS** |
| **12**| AI Parsing Fallback | LLM API key expired or unreachable | Automatically defaults to rule-based regex NLP engine. | Passed | **PASS** |
| **13**| Relative Date Resolution | Spoken: "Tomorrow at 5 PM" | Extracted `due_date`: tomorrow's calendar date (YYYY-MM-DD).| Passed | **PASS** |
| **14**| Relative Time Resolution | Spoken: "at 5 PM" or "at 10 AM" | Extracted `due_time`: "17:00" and "10:00" (24h normalized). | Passed | **PASS** |
| **15**| Urgent Task Flag | Spoken: "Urgently finish presentation"| Extracted `urgent`: `true`; red badge renders on UI. | Passed | **PASS** |
| **16**| High Priority Mapping | Spoken: "It is very important" | Extracted `priority`: `HIGH`; orange badge renders. | Passed | **PASS** |
| **17**| Normal / Low Priority | Spoken: "Not important, whenever" | Extracted `priority`: `LOW`; green badge renders. | Passed | **PASS** |
| **18**| Manual Task Creation | Click "+ Add Task" and submit form | Task saved to database; dynamic counters increment. | Passed | **PASS** |
| **19**| In-Place Task Editing | Click pencil icon, change title & due | Task updated in storage; UI updates immediately. | Passed | **PASS** |
| **20**| Complete / Reopen Task | Click circular complete button | Checkmark animates, task text strikethrough, stats update.| Passed | **PASS** |
| **21**| Delete Confirmation | Click trash icon & confirm modal | Task removed permanently from storage and DOM. | Passed | **PASS** |
| **22**| Real-Time Search | Type "Python" in search box | Filters task cards in real-time matching title/category. | Passed | **PASS** |
| **23**| Filter Pills | Click "Urgent", "Overdue", "Completed"| Shows only tasks matching the active filter category. | Passed | **PASS** |
| **24**| Mobile UI Usability | Screen width 375px (iPhone viewport) | Thumb-reachable mic, stacked stats grid, clean modals. | Passed | **PASS** |
| **25**| Desktop UI Usability | Screen width 1920px (Desktop viewport)| Spacious 5-column stats, side-by-side search & actions. | Passed | **PASS** |

---

## How to Run Automated Unit Tests
```powershell
cd backend
.\.venv\Scripts\python.exe -m unittest tests/test_api.py
```
Expected: `Ran 8 tests in ~0.5s - OK`
