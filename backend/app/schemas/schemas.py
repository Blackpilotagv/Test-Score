from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from app.models.models import UserRole, UserStatus, ExamStatus, TestStatus, PaymentStatus, PaymentMethod, AttemptStatus, PastYearPaperStatus

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: int
    name: str

class TokenData(BaseModel):
    user_id: Optional[str] = None
    role: Optional[str] = None

# User Schemas
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    mobile: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    mobile: str
    role: UserRole
    status: UserStatus
    created_at: datetime

    class Config:
        from_attributes = True

# Exam Schemas
class ExamBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    price: float = 0.0
    language_mode: str = "TA"
    status: ExamStatus = ExamStatus.ACTIVE

class ExamCreate(ExamBase):
    pass

class ExamUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    language_mode: Optional[str] = None
    status: Optional[ExamStatus] = None

class ExamOut(ExamBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Test Schemas
class TestBase(BaseModel):
    exam_id: int
    title: str
    description: Optional[str] = None
    test_date: Optional[str] = None
    duration_minutes: int = 30
    question_count: int = 50
    price: float = 29.0
    status: TestStatus = TestStatus.PUBLISHED

class TestCreate(TestBase):
    pass

class TestUpdate(BaseModel):
    exam_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    test_date: Optional[str] = None
    duration_minutes: Optional[int] = None
    question_count: Optional[int] = None
    price: Optional[float] = None
    status: Optional[TestStatus] = None

class TestOut(TestBase):
    id: int
    exam_name: Optional[str] = None
    exam_slug: Optional[str] = None
    allowed_languages: List[str] = ["ta"]
    created_at: datetime
    has_access: Optional[bool] = False
    has_active_set: Optional[bool] = False
    active_question_set_id: Optional[int] = None
    next_publish_info: Optional[str] = None

    class Config:
        from_attributes = True


# Past Year Paper Schemas
class PastYearPaperBase(BaseModel):
    exam_id: int
    year: int
    title: str
    description: Optional[str] = None
    duration_minutes: int = 180
    question_count: int = 200
    marks_per_question: float = 1.5
    negative_mark: float = 0.0
    price: float = 0.0
    status: PastYearPaperStatus = PastYearPaperStatus.DRAFT

class PastYearPaperCreate(PastYearPaperBase):
    pass

class PastYearPaperUpdate(BaseModel):
    exam_id: Optional[int] = None
    year: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    question_count: Optional[int] = None
    marks_per_question: Optional[float] = None
    negative_mark: Optional[float] = None
    price: Optional[float] = None
    status: Optional[PastYearPaperStatus] = None

class PastYearPaperOut(PastYearPaperBase):
    id: int
    exam_name: Optional[str] = None
    exam_slug: Optional[str] = None
    allowed_languages: List[str] = ["ta"]
    created_at: datetime
    updated_at: datetime
    has_access: Optional[bool] = False

    class Config:
        from_attributes = True

# Question Schemas
class QuestionBase(BaseModel):
    test_id: Optional[int] = None
    question_set_id: Optional[int] = None
    past_year_paper_id: Optional[int] = None
    question_group_id: int
    language: str  # 'ta' or 'en'
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str
    explanation: Optional[str] = None
    question_order: int = 1
    source: str = "MANUAL"
    question_source: str = "ORIGINAL"
    status: str = "ACTIVE"

class QuestionCreate(QuestionBase):
    pass

class Group2QuestionCreate(BaseModel):
    test_id: Optional[int] = None
    question_set_id: Optional[int] = None
    past_year_paper_id: Optional[int] = None
    question_order: int = 1
    question_source: str = "ORIGINAL"
    # Tamil version
    question_text_ta: str
    option_a_ta: str
    option_b_ta: str
    option_c_ta: str
    option_d_ta: str
    correct_option_ta: str
    explanation_ta: Optional[str] = None
    # English version
    question_text_en: str
    option_a_en: str
    option_b_en: str
    option_c_en: str
    option_d_en: str
    correct_option_en: str
    explanation_en: Optional[str] = None


class QuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    correct_option: Optional[str] = None
    explanation: Optional[str] = None
    question_order: Optional[int] = None
    question_source: Optional[str] = None

class QuestionClientOut(BaseModel):
    """Sent to student during test - NEVER includes correct_option or explanation"""
    id: int
    test_id: Optional[int] = None
    past_year_paper_id: Optional[int] = None
    question_group_id: int
    language: str
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    question_order: int

    class Config:
        from_attributes = True

class QuestionFullOut(QuestionBase):
    """Sent after test submission or to Admin"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Payment Schemas
class CreateOrderRequest(BaseModel):
    test_id: Optional[int] = None
    past_year_paper_id: Optional[int] = None

class ProcessMockPaymentRequest(BaseModel):
    order_id: str
    success: bool

class AdminGrantAccessRequest(BaseModel):
    user_id_or_email: str
    test_id: Optional[int] = None
    past_year_paper_id: Optional[int] = None

class PaymentOut(BaseModel):
    id: int
    user_id: int
    test_id: Optional[int] = None
    past_year_paper_id: Optional[int] = None
    test_title: Optional[str] = None
    amount: float
    gateway_order_id: Optional[str] = None
    gateway_payment_id: Optional[str] = None
    status: PaymentStatus
    payment_method: PaymentMethod
    created_at: datetime
    user_email: Optional[str] = None
    user_name: Optional[str] = None

    class Config:
        from_attributes = True

# Answer Schemas
class SaveAnswerRequest(BaseModel):
    question_group_id: int
    selected_option: Optional[str] = None

class AnswerOut(BaseModel):
    id: int
    question_group_id: int
    selected_option: Optional[str] = None
    is_correct: Optional[bool] = None

    class Config:
        from_attributes = True

# Attempt Schemas
class StartAttemptRequest(BaseModel):
    test_id: Optional[int] = None
    past_year_paper_id: Optional[int] = None
    language: str = "ta"

class SubmitAttemptRequest(BaseModel):
    pass

class AttemptOut(BaseModel):
    id: int
    test_id: Optional[int] = None
    past_year_paper_id: Optional[int] = None
    test_title: str
    duration_minutes: int
    started_at: datetime
    remaining_seconds: int
    status: AttemptStatus
    total_questions: int
    answered_count: int
    allowed_languages: List[str] = ["ta"]
    current_language: str = "ta"

    class Config:
        from_attributes = True

class QuestionReviewOut(BaseModel):
    question_group_id: int
    question_order: int
    language: str
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    student_answer: Optional[str] = None
    correct_answer: str
    status: str  # Correct, Incorrect, Unanswered
    explanation: Optional[str] = None

class ResultOut(BaseModel):
    attempt_id: int
    test_id: Optional[int] = None
    past_year_paper_id: Optional[int] = None
    test_title: str
    exam_name: str
    allowed_languages: List[str] = ["ta"]
    active_language: str = "ta"
    started_at: datetime
    submitted_at: Optional[datetime] = None
    score: float
    percentage: float
    correct_answers: int
    wrong_answers: int
    unanswered: int
    total_questions: int
    time_taken: Optional[str] = None
    questions_review: List[QuestionReviewOut] = []

    class Config:
        from_attributes = True

class AttemptSummaryOut(BaseModel):
    attempt_id: int
    test_id: Optional[int] = None
    past_year_paper_id: Optional[int] = None
    test_title: str
    exam_name: str
    submitted_at: Optional[datetime] = None
    score: float
    total_questions: int
    percentage: float
    time_taken: Optional[str] = None

# Admin Stats Schema
class AdminDashboardStats(BaseModel):
    total_students: int
    total_exams: int
    tests_published: int
    total_attempts: int
    completed_tests: int
    total_revenue: float
    today_attempts: int
    active_question_sets: Optional[int] = 0
    scheduled_question_sets: Optional[int] = 0

# QuestionSet Schemas
class QuestionSetBase(BaseModel):
    exam_id: int
    test_id: int
    title: str
    schedule_date: str  # YYYY-MM-DD (IST Date)
    status: Optional[str] = "DRAFT"

class QuestionSetCreate(QuestionSetBase):
    pass

class QuestionSetUpdate(BaseModel):
    title: Optional[str] = None
    schedule_date: Optional[str] = None
    status: Optional[str] = None

class QuestionSetOut(BaseModel):
    id: int
    exam_id: int
    test_id: int
    exam_name: Optional[str] = None
    exam_slug: Optional[str] = None
    test_title: Optional[str] = None
    title: str
    schedule_date: str
    publish_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    expire_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None
    status: str
    question_count: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SchedulerCalendarDay(BaseModel):
    date_str: str  # YYYY-MM-DD
    day_name: str  # e.g., "Monday"
    is_today: bool
    is_allowed: bool  # Within 7-day horizon
    sets: List[QuestionSetOut] = []

class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    question_set_id: Optional[int] = None
    details: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

