from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, date
from app.database.session import get_db
from app.models.models import User, UserRole, UserStatus, Exam, Test, Question, Payment, PaymentStatus, PaymentMethod, TestAttempt, AttemptStatus
from app.schemas.schemas import (
    AdminDashboardStats, ExamCreate, ExamUpdate, ExamOut,
    TestCreate, TestUpdate, TestOut, QuestionCreate, QuestionUpdate, QuestionFullOut,
    Group2QuestionCreate, AdminGrantAccessRequest, PaymentOut, UserOut
)
from app.api.deps import get_admin_user
from app.core.config import EXAM_CONFIG
from app.services.pdf_service import extract_text_from_pdf_bytes, parse_pdf_questions

router = APIRouter(prefix="/admin", tags=["Admin Portal"])

def get_next_question_group_id(db: Session) -> int:
    max_id = db.query(func.max(Question.question_group_id)).scalar()
    return (max_id or 0) + 1

@router.get("/stats", response_model=AdminDashboardStats)
def get_admin_dashboard_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    total_students = db.query(User).filter(User.role == UserRole.STUDENT).count()
    total_exams = db.query(Exam).count()
    tests_published = db.query(Test).filter(Test.status == "PUBLISHED").count()
    total_attempts = db.query(TestAttempt).count()
    completed_tests = db.query(TestAttempt).filter(TestAttempt.status == AttemptStatus.SUBMITTED).count()
    
    revenue_query = db.query(func.sum(Payment.amount)).filter(Payment.status == PaymentStatus.SUCCESS).scalar()
    total_revenue = float(revenue_query) if revenue_query else 0.0

    today_start = datetime.combine(date.today(), datetime.min.time())
    today_attempts = db.query(TestAttempt).filter(TestAttempt.created_at >= today_start).count()

    return AdminDashboardStats(
        total_students=total_students,
        total_exams=total_exams,
        tests_published=tests_published,
        total_attempts=total_attempts,
        completed_tests=completed_tests,
        total_revenue=total_revenue,
        today_attempts=today_attempts
    )

# --- EXAM MANAGEMENT ---
@router.get("/exams", response_model=List[ExamOut])
def get_admin_exams(db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    return db.query(Exam).all()

@router.post("/exams", response_model=ExamOut)
def create_exam_category(exam_in: ExamCreate, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    existing = db.query(Exam).filter(Exam.slug == exam_in.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Exam with this slug already exists")
    exam = Exam(**exam_in.model_dump())
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return exam

@router.put("/exams/{exam_id}", response_model=ExamOut)
def update_exam_category(exam_id: int, exam_in: ExamUpdate, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    update_data = exam_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(exam, field, value)
    
    db.commit()
    db.refresh(exam)
    return exam

# --- DAILY TEST MANAGEMENT ---
@router.get("/tests", response_model=List[TestOut])
def get_admin_tests(db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    tests = db.query(Test).order_by(Test.id.desc()).all()
    res = []
    for t in tests:
        res.append(TestOut(
            id=t.id,
            exam_id=t.exam_id,
            exam_name=t.exam.name if t.exam else "",
            exam_slug=t.exam.slug if t.exam else "",
            allowed_languages=["ta", "en"] if t.exam and t.exam.slug == "tnpsc-group-2" else ["ta"],
            title=t.title,
            description=t.description,
            test_date=t.test_date,
            duration_minutes=t.duration_minutes,
            question_count=t.question_count,
            price=t.price,
            status=t.status,
            created_at=t.created_at,
            has_access=True,
            has_active_set=True
        ))
    return res

@router.post("/tests", response_model=TestOut)
def create_daily_test(test_in: TestCreate, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    exam = db.query(Exam).filter(Exam.id == test_in.exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam category not found")

    test = Test(**test_in.model_dump())
    db.add(test)
    db.commit()
    db.refresh(test)
    return test

@router.put("/tests/{test_id}", response_model=TestOut)
def update_daily_test(test_id: int, test_in: TestUpdate, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    update_data = test_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(test, field, value)

    db.commit()
    db.refresh(test)
    return test

@router.delete("/tests/{test_id}")
def delete_daily_test(test_id: int, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    from app.models.models import Answer, QuestionSet
    db.query(Question).filter(Question.test_id == test_id).delete(synchronize_session=False)
    db.query(QuestionSet).filter(QuestionSet.test_id == test_id).delete(synchronize_session=False)
    
    attempts = db.query(TestAttempt).filter(TestAttempt.test_id == test_id).all()
    for att in attempts:
        db.query(Answer).filter(Answer.attempt_id == att.id).delete(synchronize_session=False)
    db.query(TestAttempt).filter(TestAttempt.test_id == test_id).delete(synchronize_session=False)
    db.query(Payment).filter(Payment.test_id == test_id).delete(synchronize_session=False)

    db.delete(test)
    db.commit()
    return {"message": "Test and all associated data deleted successfully"}


# --- QUESTION MANAGEMENT ---
@router.get("/tests/{test_id}/questions", response_model=List[QuestionFullOut])
def get_questions_for_test(test_id: int, language: Optional[str] = None, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    query = db.query(Question).filter(Question.test_id == test_id)
    if language:
        query = query.filter(Question.language == language)
    questions = query.order_by(Question.question_order.asc(), Question.language.desc()).all()
    return questions

@router.post("/questions", response_model=QuestionFullOut)
def create_single_question(q_in: QuestionCreate, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    test = db.query(Test).filter(Test.id == q_in.test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Daily test not found")

    exam_slug = test.exam.slug if test.exam else ""
    cfg = EXAM_CONFIG.get(exam_slug)
    allowed = cfg["allowed_languages"] if cfg else ["ta"]

    if q_in.language not in allowed:
        raise HTTPException(status_code=400, detail=f"Language '{q_in.language}' is not permitted for {test.exam.name}. Allowed: {allowed}")

    if not q_in.question_group_id or q_in.question_group_id <= 0:
        q_in.question_group_id = get_next_question_group_id(db)

    q = Question(**q_in.model_dump())
    db.add(q)
    db.commit()
    db.refresh(q)

    logical_count = db.query(Question.question_group_id).filter(Question.test_id == test.id).distinct().count()
    test.question_count = logical_count
    db.commit()

    return q

@router.post("/questions/group2", response_model=List[QuestionFullOut])
def create_group2_dual_question(q_in: Group2QuestionCreate, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    test = db.query(Test).filter(Test.id == q_in.test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Daily test not found")

    exam_slug = test.exam.slug if test.exam else ""
    if exam_slug != "tnpsc-group-2":
        raise HTTPException(status_code=400, detail="Dual language creation is only applicable for TNPSC Group 2 exams.")

    group_id = get_next_question_group_id(db)

    q_ta = Question(
        test_id=test.id,
        question_group_id=group_id,
        language="ta",
        question_text=q_in.question_text_ta,
        option_a=q_in.option_a_ta,
        option_b=q_in.option_b_ta,
        option_c=q_in.option_c_ta,
        option_d=q_in.option_d_ta,
        correct_option=q_in.correct_option_ta,
        explanation=q_in.explanation_ta,
        question_order=q_in.question_order,
        source="MANUAL",
        status="ACTIVE"
    )

    q_en = Question(
        test_id=test.id,
        question_group_id=group_id,
        language="en",
        question_text=q_in.question_text_en,
        option_a=q_in.option_a_en,
        option_b=q_in.option_b_en,
        option_c=q_in.option_c_en,
        option_d=q_in.option_d_en,
        correct_option=q_in.correct_option_en,
        explanation=q_in.explanation_en,
        question_order=q_in.question_order,
        source="MANUAL",
        status="ACTIVE"
    )

    db.add(q_ta)
    db.add(q_en)
    db.commit()
    db.refresh(q_ta)
    db.refresh(q_en)

    logical_count = db.query(Question.question_group_id).filter(Question.test_id == test.id).distinct().count()
    test.question_count = logical_count
    db.commit()

    return [q_ta, q_en]

# --- PDF QUESTION UPLOAD & PARSING ---
@router.post("/tests/{test_id}/upload-pdf")
async def upload_pdf_questions(
    test_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    Uploads a Question PDF file, extracts text, parses structured questions,
    assigns correct allowed language based on exam rules, and returns preview JSON.
    """
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are supported.")

    content = await file.read()
    raw_text = extract_text_from_pdf_bytes(content)
    
    exam_slug = test.exam.slug if test.exam else ""
    parsed_questions = parse_pdf_questions(raw_text, exam_slug)

    return {
        "test_id": test_id,
        "filename": file.filename,
        "exam_name": test.exam.name if test.exam else "",
        "extracted_questions_count": len(parsed_questions),
        "preview": parsed_questions
    }

@router.post("/questions/batch")
def batch_save_questions(
    questions_in: List[QuestionCreate],
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Batch saves reviewed/parsed PDF questions into DB."""
    if not questions_in:
        raise HTTPException(status_code=400, detail="No questions provided for batch save.")

    test_id = questions_in[0].test_id
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    saved_items = []
    current_group_id = get_next_question_group_id(db)
    q_set_ids = set()

    for q_item in questions_in:
        if not q_item.question_group_id or q_item.question_group_id <= 0:
            q_item.question_group_id = current_group_id
            current_group_id += 1

        if q_item.question_set_id:
            q_set_ids.add(q_item.question_set_id)

        q = Question(**q_item.model_dump())
        db.add(q)
        saved_items.append(q)

    db.commit()

    logical_count = db.query(Question.question_group_id).filter(Question.test_id == test_id).distinct().count()
    test.question_count = logical_count

    # Update QuestionSet counts if specified
    for qs_id in q_set_ids:
        from app.models.models import QuestionSet
        qs = db.query(QuestionSet).filter(QuestionSet.id == qs_id).first()
        if qs:
            qs.question_count = db.query(func.count(func.distinct(Question.question_group_id))).filter(
                Question.question_set_id == qs_id
            ).scalar() or 0

    db.commit()

    return {"message": f"Successfully saved {len(saved_items)} questions.", "total_questions": logical_count}


@router.delete("/questions/{question_id}")
def delete_question(question_id: int, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    test_id = q.test_id
    group_id = q.question_group_id

    db.query(Question).filter(Question.question_group_id == group_id, Question.test_id == test_id).delete()
    db.commit()

    logical_count = db.query(Question.question_group_id).filter(Question.test_id == test_id).distinct().count()
    test = db.query(Test).filter(Test.id == test_id).first()
    if test:
        test.question_count = logical_count
        db.commit()

    return {"message": "Question deleted for all language representations"}

# --- ADMIN MANUAL EXAM ACCESS GRANTING ---
@router.post("/grant-access")
def grant_exam_access(req: AdminGrantAccessRequest, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    user = None
    if req.user_id_or_email.isdigit():
        user = db.query(User).filter(User.id == int(req.user_id_or_email)).first()
    if not user:
        user = db.query(User).filter(User.email == req.user_id_or_email.lower()).first()

    if not user:
        raise HTTPException(status_code=404, detail="Student not found with provided ID or email")

    test = db.query(Test).filter(Test.id == req.test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    payment = db.query(Payment).filter(Payment.user_id == user.id, Payment.test_id == test.id).first()
    if not payment:
        payment = Payment(
            user_id=user.id,
            test_id=test.id,
            amount=0.0,
            gateway_order_id=f"ORDER_ADMIN_GRANT_{user.id}_{test.id}",
            gateway_payment_id=f"PAY_ADMIN_GRANTED",
            status=PaymentStatus.SUCCESS,
            payment_method=PaymentMethod.ADMIN_GRANTED
        )
        db.add(payment)
    else:
        payment.status = PaymentStatus.SUCCESS
        payment.payment_method = PaymentMethod.ADMIN_GRANTED

    db.commit()
    return {"message": f"Successfully granted access to {user.email} for test '{test.title}'."}

# --- STUDENT MANAGEMENT ---
@router.get("/students", response_model=List[UserOut])
def get_all_students(db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    students = db.query(User).filter(User.role == UserRole.STUDENT).order_by(User.id.desc()).all()
    return students

@router.put("/students/{user_id}/status")
def toggle_student_status(user_id: int, status_str: str, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Student not found")

    if status_str.upper() not in ["ACTIVE", "DISABLED"]:
        raise HTTPException(status_code=400, detail="Invalid status value")

    user.status = UserStatus(status_str.upper())
    db.commit()
    return {"message": f"Student status updated to {user.status.value}"}

# --- PAYMENT AUDIT LOGS ---
@router.get("/payments", response_model=List[PaymentOut])
def get_admin_payments(db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    payments = db.query(Payment).order_by(Payment.id.desc()).all()
    res = []
    for p in payments:
        res.append(PaymentOut(
            id=p.id,
            user_id=p.user_id,
            test_id=p.test_id,
            test_title=p.test.title if p.test else "",
            amount=p.amount,
            gateway_order_id=p.gateway_order_id,
            gateway_payment_id=p.gateway_payment_id,
            status=p.status,
            payment_method=p.payment_method,
            created_at=p.created_at,
            user_email=p.user.email if p.user else "",
            user_name=p.user.name if p.user else ""
        ))
    return res
