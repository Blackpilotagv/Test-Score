# DAILY QUESTION SCHEDULER SPECIFICATION & DOCUMENTATION

## 1. Architecture Overview

The **7-Day Rolling Daily Question Scheduler** is an automated scheduling and lifecycle management system integrated into the TNPSC Competitive Exam Mock Testing Platform.

```text
                               ┌──────────────────────────────────────────┐
                               │           React 18 + Vite + TS UI        │
                               │  (Daily Scheduler 7-Day Rolling Grid)     │
                               └────────────────────┬─────────────────────┘
                                                    │ REST API (JWT)
                               ┌────────────────────▼─────────────────────┐
                               │         FastAPI Backend Application      │
                               │  (APScheduler Cron + IST Timezone)       │
                               └────────────────────┬─────────────────────┘
                                                    │ ORM (SQLAlchemy)
                               ┌────────────────────▼─────────────────────┐
                               │   Relational DB (QuestionSet, AuditLog)  │
                               └──────────────────────────────────────────┘
```

---

## 2. Database Changes

### New Models (`app/models/models.py`)

#### `QuestionSetStatus` Enum
* `DRAFT`: Set prepared by admin, not yet scheduled.
* `SCHEDULED`: Scheduled for publication on `schedule_date` at 12:00 PM IST.
* `ACTIVE`: Currently live for students.
* `EXPIRED`: Previously active daily set, archived for attempt/history review.
* `CANCELLED`: Cancelled by admin before activation.

#### `QuestionSet` Table (`question_sets`)
* `id`: Integer Primary Key
* `exam_id`: ForeignKey(`exams.id`)
* `test_id`: ForeignKey(`tests.id`)
* `title`: String(150)
* `schedule_date`: String(10) (`YYYY-MM-DD` IST Date)
* `publish_at`: DateTime (Planned UTC 12:00 PM IST timestamp)
* `published_at`: DateTime (Actual UTC activation timestamp)
* `expire_at`: DateTime (Planned UTC expiration timestamp)
* `expired_at`: DateTime (Actual UTC expiration timestamp)
* `status`: SQLEnum(`QuestionSetStatus`)
* `question_count`: Integer
* `created_by`: ForeignKey(`users.id`)

#### `AuditLog` Table (`audit_logs`)
* `id`: Integer Primary Key
* `user_id`: ForeignKey(`users.id`)
* `action`: String(100) (e.g., `QUESTION_SET_CREATED`, `QUESTION_SET_ACTIVATED`, `QUESTION_SET_EXPIRED`, `QUESTION_SET_SCHEDULER_RECOVERY`)
* `question_set_id`: ForeignKey(`question_sets.id`)
* `details`: Text
* `created_at`: DateTime

#### Foreign Keys Added
* `Question.question_set_id`: ForeignKey(`question_sets.id`)
* `TestAttempt.question_set_id`: ForeignKey(`question_sets.id`)

---

## 3. API Endpoints

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/admin/question-sets` | Admin | List all question sets with filtering |
| `GET` | `/api/admin/question-sets/calendar` | Admin | 7-day rolling schedule grid |
| `POST` | `/api/admin/question-sets` | Admin | Create draft or scheduled set |
| `GET` | `/api/admin/question-sets/{id}` | Admin | Get detailed set view |
| `PUT` | `/api/admin/question-sets/{id}` | Admin | Update title or date before activation |
| `POST` | `/api/admin/question-sets/{id}/schedule` | Admin | Schedule set (validates 0-7 day horizon) |
| `POST` | `/api/admin/question-sets/{id}/cancel` | Admin | Cancel scheduled set |
| `POST` | `/api/admin/question-sets/{id}/publish-now` | Admin | Manual immediate activation override |
| `DELETE` | `/api/admin/question-sets/{id}` | Admin | Delete draft question set |
| `GET` | `/api/admin/question-sets/audit-logs/recent` | Admin | Fetch audit trail |

---

## 4. Scheduler Implementation & Timezone Handling

* **Timezone**: **`Asia/Kolkata` (IST)**.
* **Cron Trigger**: APScheduler `BackgroundScheduler` running every day at **12:00:00 PM IST** (`hour=12, minute=0, second=0`).
* **Timestamp Storage**: Database fields (`publish_at`, `published_at`, `expire_at`, `expired_at`, `created_at`) are stored in standard UTC.
* **Daily Status Transition Workflow**:
  ```text
  1. Expire existing ACTIVE QuestionSets -> EXPIRED
  2. Activate today's SCHEDULED QuestionSets -> ACTIVE
  3. Record audit event entries
  ```

---

## 5. Recovery Behavior & Idempotency

* **Server Startup Catch-Up**: On FastAPI boot (`@app.on_event("startup")`), `reconcile_daily_question_sets(db)` executes to reconcile missed transitions if the server was offline during 12:00 PM IST.
* **Idempotency**: Running `reconcile_daily_question_sets()` or `activate_daily_sets_transaction()` multiple times produces consistent, non-duplicate states.

---

## 6. Admin & Student Workflows

### Admin Workflow
1. Navigate to **Daily Scheduler** (`/admin/scheduler`).
2. Inspect the **7-Day Rolling Calendar View**.
3. Create a Question Set by selecting Exam, Test, and Schedule Date (validated 0-7 days ahead).
4. Add questions via PDF upload or manual entry.
5. Click **Schedule** or **Publish Now**.

### Student Workflow
1. View exam details. Available tests display availability notice ("Active set available" or "Next test starts at 12:00 PM IST").
2. Start exam attempt. Backend binds `attempt.question_set_id = active_set.id`.
3. If an active set expires while student is writing or reviewing, the attempt remains locked to `attempt.question_set_id`, ensuring questions, scoring, and solutions remain fully functional.

---

## 7. Exam Category Language Handling

* **TNPSC Group 1**: Tamil Medium only (`ta`).
* **TNPSC Group 2**: Dual Language Tamil & English (`ta`, `en`). Tamil and English versions share `question_group_id` and belong to the same `QuestionSet`. They activate and expire simultaneously.
* **TNPSC Group 4**: Tamil Medium only (`ta`).

---

## 8. Security & Concurrency

* **Authorization**: All `/api/admin/question-sets` endpoints require OAuth2 JWT tokens with `ADMIN` role.
* **Atomic Transactions**: Database operations execute inside atomic `db.commit()` / `db.rollback()` blocks.
* **Frontend Clock Decoupling**: Scheduling decisions depend strictly on the server's `Asia/Kolkata` time, ignoring client browser clocks.

---

## 9. Testing & Verification

Automated test suite (`scratch/test_scheduler.py`):
1. `test_01_horizon_and_date_validation`: Verified 0-7 day limit and rejection of past/beyond-7-day dates.
2. `test_02_scheduled_to_active_transition`: Verified QuestionSet status transitions and zero data loss on expiration.
3. `test_03_student_attempt_locking_to_question_set`: Verified historical attempts bind to `question_set_id` and remain functional.
4. `test_04_group2_dual_language_pairing`: Verified Tamil and English questions pair under `question_group_id`.
5. `test_05_reconciliation_and_idempotency`: Verified startup reconciliation is idempotent.

*Result*: **100% Passed (5/5 tests)**. Frontend build (`npm run build`) succeeded with **0 errors**.

---

## 10. Deployment Requirements & Known Limitations

* **Dependencies**: `apscheduler>=3.11.3`, `tzdata`, `tzlocal`.
* **Database**: Supported on SQLite and PostgreSQL.
* **Limitations**: High-availability multi-instance setups should use APScheduler with a distributed job store (Redis/PostgreSQL) to prevent redundant cron execution across multiple worker nodes.
