import os
from pydantic_settings import BaseSettings

EXAM_CONFIG = {
    "tnpsc-group-1": {
        "name": "TNPSC Group 1",
        "allowed_languages": ["ta"],
        "language_mode": "TA",
        "default_language": "ta"
    },
    "tnpsc-group-2": {
        "name": "TNPSC Group 2",
        "allowed_languages": ["ta", "en"],
        "language_mode": "TA_EN",
        "default_language": "ta"
    },
    "tnpsc-group-4": {
        "name": "TNPSC Group 4",
        "allowed_languages": ["ta"],
        "language_mode": "TA",
        "default_language": "ta"
    }
}

class Settings(BaseSettings):
    PROJECT_NAME: str = "TNPSC Mock Exam Platform"
    API_V1_STR: str = "/api"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./tnpsc_mock.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "tnpsc-super-secret-key-mock-exam-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    PAYMENT_MODE: str = os.getenv("PAYMENT_MODE", "MOCK")
    
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "")

    class Config:
        case_sensitive = True

settings = Settings()
