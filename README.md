# TNPSC Mock Exam Web Application

A full-stack web application designed for daily mock assessments targeting **TNPSC Group 1, Group 2, and Group 4** competitive examinations.

---

## 🌟 Supported Exams & Language Rules

| Exam Category | Medium / Allowed Languages | Language Switcher in Exam Engine | Database Storage |
| :--- | :--- | :--- | :--- |
| **TNPSC Group 1** | **Tamil Only** (`ta`) | No (Tamil Medium Only) | Stores `language = 'ta'` records ONLY |
| **TNPSC Group 2** | **Tamil + English** (`ta`, `en`) | Yes (`[ தமிழ் ] [ English ]`) | Dual records per question linked by `question_group_id` |
| **TNPSC Group 4** | **Tamil Only** (`ta`) | No (Tamil Medium Only) | Stores `language = 'ta'` records ONLY |

---

## 🚀 Application Components

- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, Lucide Icons, React Router v6, Axios.
- **Backend**: Python 3.10+, FastAPI, SQLAlchemy ORM, Pydantic v2, Passlib / PyJWT.
- **Database**: PostgreSQL / SQLite with `question_group_id` linking logical questions across languages.
- **Payment Architecture**: Modular `PaymentService` abstraction (`MockPaymentService` active in Phase 1; `ProductionPaymentService` ready for future Razorpay integration).

---

## 🔑 Default Accounts for Testing

| Role | Username / Email | Password | Features |
| :--- | :--- | :--- | :--- |
| **Student** | `student@tnpsc.com` | `student123` | Student portal, exam purchase (Mock Gateway), language switcher, test engine & dashboard |
| **Admin** | `admin@tnpsc.com` | `admin123` | Admin control panel (`/admin`), grant manual access, dual-language question editor |

---

## 🚀 Running Locally

### 1. Backend Server
```bash
cd backend
.\venv\Scripts\activate
python seed.py
uvicorn app.main:app --reload --port 8000
```
Backend API will run at `http://127.0.0.1:8000` (Docs at `http://127.0.0.1:8000/docs`).

### 2. Frontend Server
```bash
cd frontend
npm run dev
```
Frontend application will run at `http://localhost:5173`.
