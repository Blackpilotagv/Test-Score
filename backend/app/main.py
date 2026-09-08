from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.database.session import Base, engine, SessionLocal
from app.api import auth, exams, tests, payments, attempts, results, admin, admin_scheduler, past_year_papers, admin_past_year
from app.services.scheduler_service import start_scheduler, reconcile_daily_question_sets

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for TNPSC Group 1, Group 2, and Group 4 Daily Mock Exam Platform",
    version="1.0.0"
)

# CORS Middleware setup
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*"
]

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
    db = SessionLocal()
    try:
        reconcile_daily_question_sets(db)
    finally:
        db.close()
    start_scheduler()

@app.get("/")
def root():
    return {
        "message": "Welcome to TNPSC Daily Mock Exam Platform API",
        "supported_exams": ["TNPSC Group 1", "TNPSC Group 2", "TNPSC Group 4"],
        "docs_url": "/docs"
    }

