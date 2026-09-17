import pymongo
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.database.session import get_mongo_db
from app.api import auth, exams, tests, payments, attempts, results, admin, admin_scheduler, past_year_papers, admin_past_year
from app.services.scheduler_service import start_scheduler, reconcile_daily_question_sets

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Test-Score by MZAB Arcane Competitive Exam Platform",
    version="1.0.0"
)

# CORS Middleware setup
raw_origins = getattr(settings, "ALLOWED_ORIGINS", "*")
if isinstance(raw_origins, str):
    origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
else:
    origins = list(raw_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(exams.router, prefix=settings.API_V1_STR)
app.include_router(tests.router, prefix=settings.API_V1_STR)
app.include_router(payments.router, prefix=settings.API_V1_STR)
app.include_router(attempts.router, prefix=settings.API_V1_STR)
app.include_router(results.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(admin_scheduler.router, prefix=settings.API_V1_STR)
app.include_router(past_year_papers.router, prefix=settings.API_V1_STR)
app.include_router(admin_past_year.router, prefix=settings.API_V1_STR)

@app.on_event("startup")
def on_startup():
    db = get_mongo_db()
    # Create indexes for optimal querying performance
    try:
        db.users.create_index("id", unique=True)
        db.users.create_index("email", unique=True)
        db.users.create_index("mobile", unique=True)
        db.exams.create_index("id", unique=True)
        db.exams.create_index("slug", unique=True)
        db.tests.create_index("id", unique=True)
        db.past_year_papers.create_index("id", unique=True)
        db.question_sets.create_index("id", unique=True)
        db.question_sets.create_index("schedule_date")
        db.questions.create_index("id", unique=True)
        db.questions.create_index("question_group_id")
        db.payments.create_index("id", unique=True)
        db.test_attempts.create_index("id", unique=True)
        db.answers.create_index([("attempt_id", pymongo.ASCENDING), ("question_group_id", pymongo.ASCENDING)], unique=True)
    except Exception as e:
        print(f"MongoDB index setup warning: {e}")

    try:
        reconcile_daily_question_sets(db)
    except Exception as e:
        print(f"Error during startup reconciliation: {e}")

    start_scheduler()

@app.get("/")
def root():
    return {
        "message": "Welcome to Test-Score by MZAB Arcane API",
        "supported_exams": ["TNPSC Group 1", "TNPSC Group 2", "TNPSC Group 4"],
        "docs_url": "/docs"
    }
