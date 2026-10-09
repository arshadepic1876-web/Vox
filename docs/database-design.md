# Database Design Specification

This document details the storage architecture for **VOX**, detailing both the local development repository and the production **Amazon DynamoDB** NoSQL schema.

---

## 1. Storage Strategy: Abstracted Repository Pattern

To enable seamless transition from zero-setup offline development to production cloud deployment, VOX implements the Repository Pattern:

```
                  ┌──────────────────────┐
                  │     TaskService      │
                  └──────────┬───────────┘
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
┌────────────────────────┐       ┌────────────────────────┐
│ LocalJSONTaskRepository │       │ DynamoDBTaskRepository │
│   (data/tasks.json)    │       │     (AWS DynamoDB)     │
└────────────────────────┘       └────────────────────────┘
```

The active repository is controlled dynamically via `STORAGE_BACKEND` in `.env`:
* `STORAGE_BACKEND=local`: Zero AWS dependency. Fast local development.
* `STORAGE_BACKEND=dynamodb`: Scalable NoSQL cloud table.

---

## 2. Amazon DynamoDB Table Schema

* **Table Name**: `VoxTasks`
* **Partition Key (PK)**: `task_id` (String / UUID v4)
* **Sort Key (SK)**: *None (Single item lookup by unique task ID)*
* **Billing Mode**: **Pay-per-request (On-Demand)** or Free-Tier Provisioned (5 RCU, 5 WCU)

### Attribute Definitions

| Attribute Name | DynamoDB Type | Description | Sample Value |
|---|---|---|---|
| `task_id` | **S** (String, PK) | Unique identifier (UUID v4) | `"e3a269ac-3524-4a72-bf6e-4a530a40e0cd"` |
| `title` | **S** (String) | Cleaned task title | `"Submit DBMS Assignment"` |
| `description` | **S** (String) | Full details or raw transcription | `"Due tomorrow at 5 PM on university portal"`|
| `due_date` | **S** (String) | ISO Date (YYYY-MM-DD) | `"2026-10-10"` |
| `due_time` | **S** (String) | 24-Hour Time (HH:MM) | `"17:00"` |
| `priority` | **S** (String) | Priority tier: LOW, MEDIUM, HIGH, CRITICAL | `"HIGH"` |
| `urgent` | **BOOL** (Boolean) | Immediate attention required | `true` |
| `category` | **S** (String) | Domain category tag | `"College"` |
| `status` | **S** (String) | Completion status: `pending` or `completed` | `"pending"` |
| `estimated_duration_minutes` | **N** (Number) | Estimated task duration | `60` |
| `raw_transcription` | **S** (String) | Original speech-to-text transcript | `"Remind me to submit DBMS assignment..."` |
| `created_at` | **S** (String) | Timezone-aware ISO timestamp | `"2026-10-09T00:25:00+05:30"` |
| `updated_at` | **S** (String) | Last modification ISO timestamp | `"2026-10-09T00:25:00+05:30"` |

---

## 3. DynamoDB Access Patterns

| Access Pattern | DynamoDB Operation | Parameters |
|---|---|---|
| **Retrieve all tasks** | `Scan` | Scans `VoxTasks` table |
| **Get task by ID** | `GetItem` | Key: `{"task_id": "..."}` |
| **Create new task** | `PutItem` | Item: Complete task dictionary |
| **Update existing task** | `PutItem` / `UpdateItem` | Key: `{"task_id": "..."}` |
| **Delete task** | `DeleteItem` | Key: `{"task_id": "..."}` |

---

## 4. Why DynamoDB Over Relational Databases (RDS / MySQL)

1. **Serverless**: Zero server provisioning or database instances to manage.
2. **Permanent AWS Free Tier**: Offers 25 GB of storage and 25 write/read capacity units per month for free forever.
3. **Document-Oriented**: JSON payloads from Flask map 1:1 to DynamoDB attribute maps without requiring complex SQL schema migrations or ORM boilerplate.
