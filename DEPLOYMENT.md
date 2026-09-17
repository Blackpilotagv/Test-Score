# Production Deployment Guide - Test-Score by MZAB Arcane

This document provides step-by-step instructions for deploying **Test-Score by MZAB Arcane** (TNPSC Competitive Exam Mock Testing Platform) to production environments.

---

## 1. Prerequisites & MongoDB Atlas Setup

Before deploying to any cloud provider:

1. **MongoDB Atlas IP Access Whitelist**:
   - Log into your [MongoDB Atlas Console](https://cloud.mongodb.com/).
   - Navigate to **Network Access** $\rightarrow$ **IP Access List**.
   - Click **Add IP Address** and select **Allow Access from Anywhere (`0.0.0.0/0`)** (or specify your deployment server IP).
   - Save changes.

2. **Environment Variables**:
   - `MONGODB_URL`: `mongodb+srv://<username>:<password>@cluster0.ig4ngey.mongodb.net/test_score_db?appName=Cluster0`
   - `SECRET_KEY`: A strong, randomly generated string for JWT authentication.
   - `PAYMENT_MODE`: `MOCK` for testing, or `RAZORPAY` for live payments.
   - `RAZORPAY_KEY_ID` & `RAZORPAY_KEY_SECRET`: Set if using live Razorpay payments.

---

## 2. Option A: Containerized Deployment (Docker Compose)

The repository includes a ready-to-use production multi-container setup with Nginx and FastAPI.

### Steps:
1. Clone the repository on your VPS (AWS EC2, DigitalOcean droplet, Linode, Hetzner, etc.):
   ```bash
   git clone <repo-url>
   cd "mock test"
   ```

2. Create environment file:
   ```bash
   cp backend/.env.example backend/.env
   ```

3. Launch containers:
   ```bash
   docker-compose up -d --build
   ```

4. Verify services:
   - Frontend (Nginx SPA): `http://<your-server-ip>`
   - Backend (FastAPI API): `http://<your-server-ip>/api/docs`

---

## 3. Option B: Render Deployment (Blueprint)

Deploy both Frontend and Backend seamlessly on Render.com:

1. Push your repository to GitHub / GitLab.
2. In [Render Dashboard](https://dashboard.render.com/), click **New +** $\rightarrow$ **Blueprint**.
3. Connect your repository. Render will automatically detect `render.yaml`.
4. Fill in required Environment Variables:
   - `MONGODB_URL`: Your MongoDB connection string.
   - `VITE_API_BASE_URL`: URL of your backend service (e.g. `https://test-score-backend.onrender.com/api`).
5. Click **Apply**.

---

## 4. Option C: Vercel (Frontend) + Render / Railway (Backend)

### Deploying Backend on Render or Railway:
- Service Type: Web Service
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT app.main:app`
- Root Directory: `backend`

### Deploying Frontend on Vercel:
1. Import repository in [Vercel](https://vercel.com).
2. Set **Root Directory** to `frontend`.
3. Set **Framework Preset** to `Vite`.
4. Environment Variable:
   - `VITE_API_BASE_URL`: `https://your-backend-service.onrender.com/api`
5. Deploy. `vercel.json` will automatically handle SPA routing and API proxying.

---

## 5. Post-Deployment Database Seeding & Verification

To populate the initial exams (TNPSC Group 1, Group 2, Group 4), daily assessments, and 5 years' past papers (2021–2025):

Run the seed script against your production database:

```bash
cd backend
python seed.py
```

### Production Health Check
- `GET /api/` $\rightarrow$ `{"message": "Welcome to Test-Score by MZAB Arcane API", ...}`
- `GET /api/exams` $\rightarrow$ Returns active exam categories.
- `GET /api/past-year-papers` $\rightarrow$ Returns 2021–2025 question papers.
