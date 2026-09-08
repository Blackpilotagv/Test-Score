from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, Text, Boolean
from sqlalchemy.orm import relationship
import enum
from app.database.session import Base

class UserRole(str, enum.Enum):
    STUDENT = "STUDENT"
    ADMIN = "ADMIN"

class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"

class ExamStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class TestStatus(str, enum.Enum):
    PUBLISHED = "PUBLISHED"
    DRAFT = "DRAFT"

class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"

class PaymentMethod(str, enum.Enum):
    MOCK = "MOCK"
    ADMIN_GRANTED = "ADMIN_GRANTED"
    RAZORPAY = "RAZORPAY"

class AttemptStatus(str, enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    EXPIRED = "EXPIRED"

class QuestionSetStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"

class PastYearPaperStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    REVIEW = "REVIEW"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    mobile = Column(String(20), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.STUDENT, nullable=False)
    status = Column(SQLEnum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    payments = relationship("Payment", back_populates="user")
    attempts = relationship("TestAttempt", back_populates="user")

class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # TNPSC Group 1, Group 2, Group 4
    slug = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, default=0.0, nullable=False)
    language_mode = Column(String(20), default="TA", nullable=False)  # TA or TA_EN
    status = Column(SQLEnum(ExamStatus), default=ExamStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tests = relationship("Test", back_populates="exam", cascade="all, delete-orphan")
    question_sets = relationship("QuestionSet", back_populates="exam", cascade="all, delete-orphan")
    past_year_papers = relationship("PastYearPaper", back_populates="exam", cascade="all, delete-orphan")

class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    test_date = Column(String(20), nullable=True)
    duration_minutes = Column(Integer, default=30, nullable=False)
    question_count = Column(Integer, default=50, nullable=False)  # Number of logical questions
    price = Column(Float, default=29.0, nullable=False)
    status = Column(SQLEnum(TestStatus), default=TestStatus.PUBLISHED, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    exam = relationship("Exam", back_populates="tests")
    questions = relationship("Question", back_populates="test", cascade="all, delete-orphan")
    question_sets = relationship("QuestionSet", back_populates="test", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="test")
    attempts = relationship("TestAttempt", back_populates="test")

class PastYearPaper(Base):
    __tablename__ = "past_year_papers"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    year = Column(Integer, nullable=False, index=True)               # e.g., 2025, 2024, 2023, 2022, 2021
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, default=180, nullable=False)
    question_count = Column(Integer, default=200, nullable=False)
    marks_per_question = Column(Float, default=1.5, nullable=False)
    negative_mark = Column(Float, default=0.0, nullable=False)
    price = Column(Float, default=0.0, nullable=False)
    status = Column(SQLEnum(PastYearPaperStatus), default=PastYearPaperStatus.DRAFT, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    exam = relationship("Exam", back_populates="past_year_papers")
    questions = relationship("Question", back_populates="past_year_paper", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="past_year_paper")
    attempts = relationship("TestAttempt", back_populates="past_year_paper")

class QuestionSet(Base):
    __tablename__ = "question_sets"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    title = Column(String(150), nullable=False)
    schedule_date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD (IST Date)
    publish_at = Column(DateTime, nullable=True)                      # UTC timestamp for 12:00 PM IST on schedule_date
    published_at = Column(DateTime, nullable=True)                    # Actual UTC activation time
    expire_at = Column(DateTime, nullable=True)                       # UTC timestamp for 12:00 PM IST on schedule_date + 1 day
    expired_at = Column(DateTime, nullable=True)                      # Actual UTC expiration time
    status = Column(SQLEnum(QuestionSetStatus), default=QuestionSetStatus.DRAFT, nullable=False)
    question_count = Column(Integer, default=0, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    exam = relationship("Exam", back_populates="question_sets")
    test = relationship("Test", back_populates="question_sets")
    questions = relationship("Question", back_populates="question_set", cascade="all, delete-orphan")
    attempts = relationship("TestAttempt", back_populates="question_set")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=True)
    question_set_id = Column(Integer, ForeignKey("question_sets.id"), nullable=True)
    past_year_paper_id = Column(Integer, ForeignKey("past_year_papers.id"), nullable=True)
    question_group_id = Column(Integer, index=True, nullable=False)  # Links logical question across languages
    language = Column(String(5), index=True, nullable=False)           # 'ta' or 'en'
    question_text = Column(Text, nullable=False)
    option_a = Column(Text, nullable=False)
    option_b = Column(Text, nullable=False)
    option_c = Column(Text, nullable=False)
    option_d = Column(Text, nullable=False)
    correct_option = Column(String(5), nullable=False)                 # A, B, C, D
    explanation = Column(Text, nullable=True)
    question_order = Column(Integer, default=1, nullable=False)        # Logical order (1..N)
    source = Column(String(20), default="MANUAL", nullable=False)       # MANUAL, PDF, AI
    question_source = Column(String(50), default="ORIGINAL", nullable=False) # ORIGINAL, AI_GENERATED, AI_TRANSLATED, MANUAL
    status = Column(String(20), default="ACTIVE", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    test = relationship("Test", back_populates="questions")
    question_set = relationship("QuestionSet", back_populates="questions")
    past_year_paper = relationship("PastYearPaper", back_populates="questions")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=True)
    past_year_paper_id = Column(Integer, ForeignKey("past_year_papers.id"), nullable=True)
    amount = Column(Float, nullable=False)
    gateway_order_id = Column(String(100), nullable=True)
    gateway_payment_id = Column(String(100), nullable=True)
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    payment_method = Column(SQLEnum(PaymentMethod), default=PaymentMethod.MOCK, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="payments")
    test = relationship("Test", back_populates="payments")
    past_year_paper = relationship("PastYearPaper", back_populates="payments")

class TestAttempt(Base):
    __tablename__ = "test_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=True)
    question_set_id = Column(Integer, ForeignKey("question_sets.id"), nullable=True)
    past_year_paper_id = Column(Integer, ForeignKey("past_year_papers.id"), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    submitted_at = Column(DateTime, nullable=True)
    status = Column(SQLEnum(AttemptStatus), default=AttemptStatus.IN_PROGRESS, nullable=False)
    score = Column(Float, default=0.0)
    correct_answers = Column(Integer, default=0)
    wrong_answers = Column(Integer, default=0)
    unanswered = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    percentage = Column(Float, default=0.0)
    time_taken = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="attempts")
    test = relationship("Test", back_populates="attempts")
    question_set = relationship("QuestionSet", back_populates="attempts")
    past_year_paper = relationship("PastYearPaper", back_populates="attempts")
    answers = relationship("Answer", back_populates="attempt", cascade="all, delete-orphan")

class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("test_attempts.id"), nullable=False)
    question_group_id = Column(Integer, index=True, nullable=False)  # Logical question group ID
    selected_option = Column(String(5), nullable=True)                # A, B, C, D or None
    is_correct = Column(Boolean, nullable=True)
    answered_at = Column(DateTime, default=datetime.utcnow)

    attempt = relationship("TestAttempt", back_populates="answers")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    question_set_id = Column(Integer, ForeignKey("question_sets.id"), nullable=True)
    past_year_paper_id = Column(Integer, ForeignKey("past_year_papers.id"), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

