from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pymongo import DESCENDING, ASCENDING

from app.database.session import get_db, get_next_sequence
from app.models.models import (
    UserRole, UserStatus, ExamStatus, TestStatus, PaymentStatus, PaymentMethod, AttemptStatus, to_mongo_doc
)
from app.schemas.schemas import (
    AdminDashboardStats, ExamCreate, ExamUpdate, ExamOut,
    TestCreate, TestUpdate, TestOut, QuestionCreate, QuestionUpdate, QuestionFullOut,
    Group2QuestionCreate, AdminGrantAccessRequest, PaymentOut, UserOut
)
from app.api.deps import get_admin_user
from app.core.config import EXAM_CONFIG
from app.services.pdf_service import extract_text_from_pdf_bytes, parse_pdf_questions

router = APIRouter(prefix="/admin", tags=["Admin Portal"])

def get_next_question_group_id(db) -> int:
    return get_next_sequence(db, "question_group_id")

@router.get("/stats", response_model=AdminDashboardStats)
def get_admin_dashboard_stats(
    db = Depends(get_db),
    admin = Depends(get_admin_user)
):
    total_students = db.users.count_documents({"role": UserRole.STUDENT})
    total_exams = db.exams.count_documents({})
    tests_published = db.tests.count_documents({"status": "PUBLISHED"})
    total_attempts = db.test_attempts.count_documents({})
    completed_tests = db.test_attempts.count_documents({"status": AttemptStatus.SUBMITTED})

    pipeline = [
        {"$match": {"status": PaymentStatus.SUCCESS}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    revenue_agg = list(db.payments.aggregate(pipeline))
    total_revenue = float(revenue_agg[0]["total"]) if revenue_agg else 0.0

    today_start = datetime.combine(date.today(), datetime.min.time())
    today_attempts = db.test_attempts.count_documents({"created_at": {"$gte": today_start}})

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
def get_admin_exams(db = Depends(get_db), admin = Depends(get_admin_user)):
    exam_docs = list(db.exams.find({}))
    return [to_mongo_doc(e) for e in exam_docs]

@router.post("/exams", response_model=ExamOut)
def create_exam_category(exam_in: ExamCreate, db = Depends(get_db), admin = Depends(get_admin_user)):
    if db.exams.find_one({"slug": exam_in.slug}):
        raise HTTPException(status_code=400, detail="Exam with this slug already exists")

    exam_id = get_next_sequence(db, "exam_id")
    now = datetime.utcnow()
    exam_doc = {
        "id": exam_id,
        "name": exam_in.name,
        "slug": exam_in.slug,
        "description": exam_in.description,
        "price": exam_in.price,
        "language_mode": exam_in.language_mode,
        "status": exam_in.status if hasattr(exam_in, 'status') else ExamStatus.ACTIVE,
        "created_at": now,
        "updated_at": now
    }
    db.exams.insert_one(exam_doc)
    return to_mongo_doc(exam_doc)

@router.put("/exams/{exam_id}", response_model=ExamOut)
def update_exam_category(exam_id: int, exam_in: ExamUpdate, db = Depends(get_db), admin = Depends(get_admin_user)):
    exam_doc = db.exams.find_one({"id": exam_id})
    if not exam_doc:
        raise HTTPException(status_code=404, detail="Exam not found")

    update_data = exam_in.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()

    db.exams.update_one({"id": exam_id}, {"$set": update_data})
    updated_doc = db.exams.find_one({"id": exam_id})
    return to_mongo_doc(updated_doc)

# --- DAILY TEST MANAGEMENT ---
@router.get("/tests", response_model=List[TestOut])
def get_admin_tests(db = Depends(get_db), admin = Depends(get_admin_user)):
    test_docs = list(db.tests.find({}, sort=[("id", DESCENDING)]))
    res = []
    for t_doc in test_docs:
        t = to_mongo_doc(t_doc)
        exam_doc = db.exams.find_one({"id": t.exam_id}) if t.exam_id else None
        exam_name = exam_doc["name"] if exam_doc else ""
        exam_slug = exam_doc["slug"] if exam_doc else ""
        res.append(TestOut(
            id=t.id,
            exam_id=t.exam_id,
            exam_name=exam_name,
            exam_slug=exam_slug,
            allowed_languages=["ta", "en"] if exam_slug == "tnpsc-group-2" else ["ta"],
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
def create_daily_test(test_in: TestCreate, db = Depends(get_db), admin = Depends(get_admin_user)):
    exam_doc = db.exams.find_one({"id": test_in.exam_id})
    if not exam_doc:
        raise HTTPException(status_code=404, detail="Exam category not found")

    test_id = get_next_sequence(db, "test_id")
    now = datetime.utcnow()
    test_doc = {
        "id": test_id,
        "exam_id": test_in.exam_id,
        "title": test_in.title,
        "description": test_in.description,
        "test_date": test_in.test_date,
        "duration_minutes": test_in.duration_minutes,
        "question_count": test_in.question_count,
        "price": test_in.price,
        "status": test_in.status if hasattr(test_in, 'status') else TestStatus.PUBLISHED,
        "created_at": now,
        "updated_at": now
    }
    db.tests.insert_one(test_doc)
    
    t = to_mongo_doc(test_doc)
    exam_name = exam_doc["name"]
    exam_slug = exam_doc["slug"]
    return TestOut(
        id=t.id,
        exam_id=t.exam_id,
        exam_name=exam_name,
        exam_slug=exam_slug,
        allowed_languages=["ta", "en"] if exam_slug == "tnpsc-group-2" else ["ta"],
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
    )

@router.put("/tests/{test_id}", response_model=TestOut)
def update_daily_test(test_id: int, test_in: TestUpdate, db = Depends(get_db), admin = Depends(get_admin_user)):
    test_doc = db.tests.find_one({"id": test_id})
    if not test_doc:
        raise HTTPException(status_code=404, detail="Test not found")

    update_data = test_in.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()

    db.tests.update_one({"id": test_id}, {"$set": update_data})
    updated_doc = db.tests.find_one({"id": test_id})
    t = to_mongo_doc(updated_doc)
    exam_doc = db.exams.find_one({"id": t.exam_id}) if t.exam_id else None
    return TestOut(
        id=t.id,
        exam_id=t.exam_id,
        exam_name=exam_doc["name"] if exam_doc else "",
        exam_slug=exam_doc["slug"] if exam_doc else "",
        allowed_languages=["ta", "en"] if exam_doc and exam_doc["slug"] == "tnpsc-group-2" else ["ta"],
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
    )

@router.delete("/tests/{test_id}")
def delete_daily_test(test_id: int, db = Depends(get_db), admin = Depends(get_admin_user)):
    test_doc = db.tests.find_one({"id": test_id})
    if not test_doc:
        raise HTTPException(status_code=404, detail="Test not found")

    db.questions.delete_many({"test_id": test_id})
    db.question_sets.delete_many({"test_id": test_id})

    attempt_docs = list(db.test_attempts.find({"test_id": test_id}))
    attempt_ids = [a["id"] for a in attempt_docs]
    if attempt_ids:
        db.answers.delete_many({"attempt_id": {"$in": attempt_ids}})
    db.test_attempts.delete_many({"test_id": test_id})
    db.payments.delete_many({"test_id": test_id})
    db.tests.delete_one({"id": test_id})

    return {"message": "Test and all associated data deleted successfully"}

# --- QUESTION MANAGEMENT ---
@router.get("/tests/{test_id}/questions", response_model=List[QuestionFullOut])
def get_questions_for_test(test_id: int, language: Optional[str] = None, db = Depends(get_db), admin = Depends(get_admin_user)):
    query_filter = {"test_id": test_id}
    if language:
        query_filter["language"] = language

    q_docs = list(db.questions.find(query_filter, sort=[("question_order", ASCENDING), ("language", DESCENDING)]))
    return [to_mongo_doc(q) for q in q_docs]

@router.post("/questions", response_model=QuestionFullOut)
def create_single_question(q_in: QuestionCreate, db = Depends(get_db), admin = Depends(get_admin_user)):
    test_doc = db.tests.find_one({"id": q_in.test_id})
    if not test_doc:
        raise HTTPException(status_code=404, detail="Daily test not found")

    exam_doc = db.exams.find_one({"id": test_doc["exam_id"]}) if test_doc.get("exam_id") else None
    exam_slug = exam_doc["slug"] if exam_doc else ""
    cfg = EXAM_CONFIG.get(exam_slug)
    allowed = cfg["allowed_languages"] if cfg else ["ta"]

    if q_in.language not in allowed:
        exam_name = exam_doc["name"] if exam_doc else "this exam"
        raise HTTPException(status_code=400, detail=f"Language '{q_in.language}' is not permitted for {exam_name}. Allowed: {allowed}")

    if not q_in.question_group_id or q_in.question_group_id <= 0:
        q_in.question_group_id = get_next_question_group_id(db)

    q_id = get_next_sequence(db, "question_id")
    now = datetime.utcnow()
    q_doc = {
        "id": q_id,
        "test_id": q_in.test_id,
        "question_set_id": q_in.question_set_id,
        "past_year_paper_id": q_in.past_year_paper_id,
        "question_group_id": q_in.question_group_id,
        "language": q_in.language,
        "question_text": q_in.question_text,
        "option_a": q_in.option_a,
        "option_b": q_in.option_b,
        "option_c": q_in.option_c,
        "option_d": q_in.option_d,
        "correct_option": q_in.correct_option,
        "explanation": q_in.explanation,
        "question_order": q_in.question_order,
        "source": q_in.source if hasattr(q_in, 'source') else "MANUAL",
        "question_source": getattr(q_in, 'question_source', "ORIGINAL"),
        "status": "ACTIVE",
        "created_at": now,
        "updated_at": now
    }
    db.questions.insert_one(q_doc)

    groups = db.questions.distinct("question_group_id", {"test_id": q_in.test_id})
    db.tests.update_one({"id": q_in.test_id}, {"$set": {"question_count": len(groups)}})

    return to_mongo_doc(q_doc)

@router.post("/questions/group2", response_model=List[QuestionFullOut])
def create_group2_dual_question(q_in: Group2QuestionCreate, db = Depends(get_db), admin = Depends(get_admin_user)):
    test_doc = db.tests.find_one({"id": q_in.test_id})
    if not test_doc:
        raise HTTPException(status_code=404, detail="Daily test not found")

    exam_doc = db.exams.find_one({"id": test_doc["exam_id"]}) if test_doc.get("exam_id") else None
    exam_slug = exam_doc["slug"] if exam_doc else ""
    if exam_slug != "tnpsc-group-2":
        raise HTTPException(status_code=400, detail="Dual language creation is only applicable for TNPSC Group 2 exams.")

    group_id = get_next_question_group_id(db)
    now = datetime.utcnow()

    q_ta_id = get_next_sequence(db, "question_id")
    q_ta_doc = {
        "id": q_ta_id,
        "test_id": q_in.test_id,
        "question_set_id": None,
        "past_year_paper_id": None,
        "question_group_id": group_id,
        "language": "ta",
        "question_text": q_in.question_text_ta,
        "option_a": q_in.option_a_ta,
        "option_b": q_in.option_b_ta,
        "option_c": q_in.option_c_ta,
        "option_d": q_in.option_d_ta,
        "correct_option": q_in.correct_option_ta,
        "explanation": q_in.explanation_ta,
        "question_order": q_in.question_order,
        "source": "MANUAL",
        "question_source": "ORIGINAL",
        "status": "ACTIVE",
        "created_at": now,
        "updated_at": now
    }

    q_en_id = get_next_sequence(db, "question_id")
    q_en_doc = {
        "id": q_en_id,
        "test_id": q_in.test_id,
        "question_set_id": None,
        "past_year_paper_id": None,
        "question_group_id": group_id,
        "language": "en",
        "question_text": q_in.question_text_en,
        "option_a": q_in.option_a_en,
        "option_b": q_in.option_b_en,
        "option_c": q_in.option_c_en,
        "option_d": q_in.option_d_en,
        "correct_option": q_in.correct_option_en,
        "explanation": q_in.explanation_en,
        "question_order": q_in.question_order,
        "source": "MANUAL",
        "question_source": "ORIGINAL",
        "status": "ACTIVE",
        "created_at": now,
        "updated_at": now
    }

    db.questions.insert_one(q_ta_doc)
    db.questions.insert_one(q_en_doc)

    groups = db.questions.distinct("question_group_id", {"test_id": q_in.test_id})
    db.tests.update_one({"id": q_in.test_id}, {"$set": {"question_count": len(groups)}})

    return [to_mongo_doc(q_ta_doc), to_mongo_doc(q_en_doc)]

# --- PDF QUESTION UPLOAD & PARSING ---
@router.post("/tests/{test_id}/upload-pdf")
async def upload_pdf_questions(
    test_id: int,
    file: UploadFile = File(...),
    db = Depends(get_db),
    admin = Depends(get_admin_user)
):
    test_doc = db.tests.find_one({"id": test_id})
    if not test_doc:
        raise HTTPException(status_code=404, detail="Test not found")

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are supported.")

    content = await file.read()
    raw_text = extract_text_from_pdf_bytes(content)
    
    exam_doc = db.exams.find_one({"id": test_doc["exam_id"]}) if test_doc.get("exam_id") else None
    exam_slug = exam_doc["slug"] if exam_doc else ""
    parsed_questions = parse_pdf_questions(raw_text, exam_slug)

    exam_name = exam_doc["name"] if exam_doc else ""

    return {
        "test_id": test_id,
        "filename": file.filename,
        "exam_name": exam_name,
        "extracted_questions_count": len(parsed_questions),
        "preview": parsed_questions
    }

@router.post("/questions/batch")
def batch_save_questions(
    questions_in: List[QuestionCreate],
    db = Depends(get_db),
    admin = Depends(get_admin_user)
):
    if not questions_in:
        raise HTTPException(status_code=400, detail="No questions provided for batch save.")

    test_id = questions_in[0].test_id
    test_doc = db.tests.find_one({"id": test_id})
    if not test_doc:
        raise HTTPException(status_code=404, detail="Test not found")

    current_group_id = get_next_question_group_id(db)
    q_set_ids = set()
    now = datetime.utcnow()

    for q_item in questions_in:
        if not q_item.question_group_id or q_item.question_group_id <= 0:
            q_item.question_group_id = current_group_id
            current_group_id += 1

        if q_item.question_set_id:
            q_set_ids.add(q_item.question_set_id)

        q_id = get_next_sequence(db, "question_id")
        q_doc = {
            "id": q_id,
            "test_id": q_item.test_id,
            "question_set_id": q_item.question_set_id,
            "past_year_paper_id": q_item.past_year_paper_id,
            "question_group_id": q_item.question_group_id,
            "language": q_item.language,
            "question_text": q_item.question_text,
            "option_a": q_item.option_a,
            "option_b": q_item.option_b,
            "option_c": q_item.option_c,
            "option_d": q_item.option_d,
            "correct_option": q_item.correct_option,
            "explanation": q_item.explanation,
            "question_order": q_item.question_order,
            "source": getattr(q_item, 'source', "MANUAL"),
            "question_source": getattr(q_item, 'question_source', "ORIGINAL"),
            "status": "ACTIVE",
            "created_at": now,
            "updated_at": now
        }
        db.questions.insert_one(q_doc)

    groups = db.questions.distinct("question_group_id", {"test_id": test_id})
    logical_count = len(groups)
    db.tests.update_one({"id": test_id}, {"$set": {"question_count": logical_count}})

    for qs_id in q_set_ids:
        qs_groups = db.questions.distinct("question_group_id", {"question_set_id": qs_id})
        db.question_sets.update_one({"id": qs_id}, {"$set": {"question_count": len(qs_groups)}})

    return {"message": f"Successfully saved {len(questions_in)} questions.", "total_questions": logical_count}

@router.delete("/questions/{question_id}")
def delete_question(question_id: int, db = Depends(get_db), admin = Depends(get_admin_user)):
    q_doc = db.questions.find_one({"id": question_id})
    if not q_doc:
        raise HTTPException(status_code=404, detail="Question not found")

    test_id = q_doc["test_id"]
    group_id = q_doc["question_group_id"]

    db.questions.delete_many({"question_group_id": group_id, "test_id": test_id})

    groups = db.questions.distinct("question_group_id", {"test_id": test_id})
    db.tests.update_one({"id": test_id}, {"$set": {"question_count": len(groups)}})

    return {"message": "Question deleted for all language representations"}

# --- ADMIN MANUAL EXAM ACCESS GRANTING ---
@router.post("/grant-access")
def grant_exam_access(req: AdminGrantAccessRequest, db = Depends(get_db), admin = Depends(get_admin_user)):
    user_doc = None
    if req.user_id_or_email.isdigit():
        user_doc = db.users.find_one({"id": int(req.user_id_or_email)})
    if not user_doc:
        user_doc = db.users.find_one({"email": req.user_id_or_email.lower()})

    if not user_doc:
        raise HTTPException(status_code=404, detail="Student not found with provided ID or email")

    user = to_mongo_doc(user_doc)
    test_doc = db.tests.find_one({"id": req.test_id})
    if not test_doc:
        raise HTTPException(status_code=404, detail="Test not found")

    payment_doc = db.payments.find_one({"user_id": user.id, "test_id": req.test_id})
    now = datetime.utcnow()
    if not payment_doc:
        payment_id = get_next_sequence(db, "payment_id")
        db.payments.insert_one({
            "id": payment_id,
            "user_id": user.id,
            "test_id": req.test_id,
            "past_year_paper_id": None,
            "amount": 0.0,
            "gateway_order_id": f"ORDER_ADMIN_GRANT_{user.id}_{req.test_id}",
            "gateway_payment_id": "PAY_ADMIN_GRANTED",
            "status": PaymentStatus.SUCCESS,
            "payment_method": PaymentMethod.ADMIN_GRANTED,
            "created_at": now
        })
    else:
        db.payments.update_one(
            {"id": payment_doc["id"]},
            {"$set": {"status": PaymentStatus.SUCCESS, "payment_method": PaymentMethod.ADMIN_GRANTED}}
        )

    return {"message": f"Successfully granted access to {user.email} for test '{test_doc['title']}'."}

# --- STUDENT MANAGEMENT ---
@router.get("/students", response_model=List[UserOut])
def get_all_students(db = Depends(get_db), admin = Depends(get_admin_user)):
    student_docs = list(db.users.find({"role": UserRole.STUDENT}, sort=[("id", DESCENDING)]))
    return [to_mongo_doc(s) for s in student_docs]

@router.put("/students/{user_id}/status")
def toggle_student_status(user_id: int, status_str: str, db = Depends(get_db), admin = Depends(get_admin_user)):
    user_doc = db.users.find_one({"id": user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="Student not found")

    if status_str.upper() not in ["ACTIVE", "DISABLED"]:
        raise HTTPException(status_code=400, detail="Invalid status value")

    db.users.update_one({"id": user_id}, {"$set": {"status": status_str.upper()}})
    return {"message": f"Student status updated to {status_str.upper()}"}

# --- PAYMENT AUDIT LOGS ---
@router.get("/payments", response_model=List[PaymentOut])
def get_admin_payments(db = Depends(get_db), admin = Depends(get_admin_user)):
    payment_docs = list(db.payments.find({}, sort=[("id", DESCENDING)]))
    res = []
    for p_doc in payment_docs:
        p = to_mongo_doc(p_doc)
        test_title = ""
        if p.past_year_paper_id:
            paper_doc = db.past_year_papers.find_one({"id": p.past_year_paper_id})
            test_title = paper_doc["title"] if paper_doc else ""
        elif p.test_id:
            test_doc = db.tests.find_one({"id": p.test_id})
            test_title = test_doc["title"] if test_doc else ""

        user_doc = db.users.find_one({"id": p.user_id}) if p.user_id else None

        res.append(PaymentOut(
            id=p.id,
            user_id=p.user_id,
            test_id=p.test_id,
            past_year_paper_id=p.past_year_paper_id,
            test_title=test_title,
            amount=p.amount,
            gateway_order_id=p.gateway_order_id,
            gateway_payment_id=p.gateway_payment_id,
            status=p.status,
            payment_method=p.payment_method,
            created_at=p.created_at,
            user_email=user_doc["email"] if user_doc else "",
            user_name=user_doc["name"] if user_doc else ""
        ))
    return res
