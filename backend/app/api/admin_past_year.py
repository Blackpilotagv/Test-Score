from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pymongo import DESCENDING, ASCENDING

from app.database.session import get_db, get_next_sequence
from app.models.models import (
    PastYearPaperStatus, PaymentStatus, PaymentMethod, to_mongo_doc
)
from app.schemas.schemas import (
    PastYearPaperCreate, PastYearPaperUpdate, PastYearPaperOut,
    QuestionCreate, Group2QuestionCreate, QuestionFullOut,
    AdminGrantAccessRequest
)
from app.api.deps import get_admin_user
from app.services.pdf_service import extract_text_from_pdf_bytes, parse_pdf_questions
from app.core.config import EXAM_CONFIG

router = APIRouter(prefix="/admin/past-year-papers", tags=["Admin Past Year Papers"])

@router.get("", response_model=List[PastYearPaperOut])
def get_all_past_year_papers(
    exam_id: Optional[int] = None,
    year: Optional[int] = None,
    paper_status: Optional[str] = None,
    db = Depends(get_db),
    admin = Depends(get_admin_user)
):
    query_filter = {}
    if exam_id:
        query_filter["exam_id"] = exam_id
    if year:
        query_filter["year"] = year
    if paper_status:
        query_filter["status"] = paper_status.upper()

    paper_docs = list(db.past_year_papers.find(
        query_filter,
        sort=[("year", DESCENDING), ("id", DESCENDING)]
    ))
    out = []
    for p_doc in paper_docs:
        p = to_mongo_doc(p_doc)
        exam_doc = db.exams.find_one({"id": p.exam_id}) if p.exam_id else None
        exam_name = exam_doc["name"] if exam_doc else ""
        exam_slug = exam_doc["slug"] if exam_doc else ""
        cfg = EXAM_CONFIG.get(exam_slug)
        allowed_langs = cfg["allowed_languages"] if cfg else ["ta"]

        out.append(PastYearPaperOut(
            id=p.id,
            exam_id=p.exam_id,
            year=p.year,
            title=p.title,
            description=p.description,
            duration_minutes=p.duration_minutes,
            question_count=p.question_count,
            marks_per_question=p.marks_per_question,
            negative_mark=p.negative_mark,
            price=p.price,
            status=p.status,
            exam_name=exam_name,
            exam_slug=exam_slug,
            allowed_languages=allowed_langs,
            created_at=p.created_at,
            updated_at=p.updated_at
        ))
    return out

@router.post("", response_model=PastYearPaperOut)
def create_past_year_paper(
    req: PastYearPaperCreate,
    db = Depends(get_db),
    admin = Depends(get_admin_user)
):
    exam_doc = db.exams.find_one({"id": req.exam_id})
    if not exam_doc:
        raise HTTPException(status_code=404, detail="Exam category not found")

    paper_id = get_next_sequence(db, "past_year_paper_id")
    now = datetime.utcnow()
    paper_doc = {
        "id": paper_id,
        "exam_id": req.exam_id,
        "year": req.year,
        "title": req.title,
        "description": req.description,
        "duration_minutes": req.duration_minutes,
        "question_count": req.question_count,
        "marks_per_question": req.marks_per_question,
        "negative_mark": req.negative_mark,
        "price": req.price,
        "status": req.status if hasattr(req, 'status') else PastYearPaperStatus.DRAFT,
        "created_by": admin.id,
        "created_at": now,
        "updated_at": now
    }
    db.past_year_papers.insert_one(paper_doc)
    paper = to_mongo_doc(paper_doc)

    log_id = get_next_sequence(db, "audit_log_id")
    db.audit_logs.insert_one({
        "id": log_id,
        "user_id": admin.id,
        "action": "CREATE_PAST_YEAR_PAPER",
        "past_year_paper_id": paper.id,
        "details": f"Created Past Year Paper '{paper.title}' for {exam_doc['name']} ({paper.year})",
        "created_at": now
    })

    cfg = EXAM_CONFIG.get(exam_doc["slug"])
    allowed_langs = cfg["allowed_languages"] if cfg else ["ta"]

    return PastYearPaperOut(
        id=paper.id,
        exam_id=paper.exam_id,
        year=paper.year,
        title=paper.title,
        description=paper.description,
        duration_minutes=paper.duration_minutes,
        question_count=paper.question_count,
        marks_per_question=paper.marks_per_question,
        negative_mark=paper.negative_mark,
        price=paper.price,
        status=paper.status,
        exam_name=exam_doc["name"],
        exam_slug=exam_doc["slug"],
        allowed_languages=allowed_langs,
        created_at=paper.created_at,
        updated_at=paper.updated_at
    )

@router.get("/{paper_id}")
def get_past_year_paper_details(
    paper_id: int,
    db = Depends(get_db),
    admin = Depends(get_admin_user)
):
    paper_doc = db.past_year_papers.find_one({"id": paper_id})
    if not paper_doc:
        raise HTTPException(status_code=404, detail="Past year paper not found")
    paper = to_mongo_doc(paper_doc)

    q_docs = list(db.questions.find(
        {"past_year_paper_id": paper.id},
        sort=[("question_order", ASCENDING), ("language", ASCENDING)]
    ))

    exam_doc = db.exams.find_one({"id": paper.exam_id}) if paper.exam_id else None
    exam_name = exam_doc["name"] if exam_doc else ""
    exam_slug = exam_doc["slug"] if exam_doc else ""
    cfg = EXAM_CONFIG.get(exam_slug)
    allowed_langs = cfg["allowed_languages"] if cfg else ["ta"]

    q_outs = [QuestionFullOut.model_validate(q) for q in q_docs]

    return {
        "paper": PastYearPaperOut(
            id=paper.id,
            exam_id=paper.exam_id,
            year=paper.year,
            title=paper.title,
            description=paper.description,
            duration_minutes=paper.duration_minutes,
            question_count=paper.question_count,
            marks_per_question=paper.marks_per_question,
            negative_mark=paper.negative_mark,
            price=paper.price,
            status=paper.status,
            exam_name=exam_name,
            exam_slug=exam_slug,
            allowed_languages=allowed_langs,
            created_at=paper.created_at,
            updated_at=paper.updated_at
        ),
        "questions": q_outs
    }

@router.put("/{paper_id}", response_model=PastYearPaperOut)
def update_past_year_paper(
    paper_id: int,
    req: PastYearPaperUpdate,
    db = Depends(get_db),
    admin = Depends(get_admin_user)
):
    paper_doc = db.past_year_papers.find_one({"id": paper_id})
    if not paper_doc:
        raise HTTPException(status_code=404, detail="Past year paper not found")

    update_fields = req.model_dump(exclude_unset=True)
    update_fields["updated_at"] = datetime.utcnow()

    db.past_year_papers.update_one({"id": paper_id}, {"$set": update_fields})
    updated_doc = db.past_year_papers.find_one({"id": paper_id})
    paper = to_mongo_doc(updated_doc)

    now = datetime.utcnow()
    log_id = get_next_sequence(db, "audit_log_id")
    db.audit_logs.insert_one({
        "id": log_id,
        "user_id": admin.id,
        "action": "UPDATE_PAST_YEAR_PAPER",
        "past_year_paper_id": paper.id,
        "details": f"Updated Past Year Paper status/metadata to {paper.status}",
        "created_at": now
    })

    exam_doc = db.exams.find_one({"id": paper.exam_id}) if paper.exam_id else None
    exam_name = exam_doc["name"] if exam_doc else ""
    exam_slug = exam_doc["slug"] if exam_doc else ""
    cfg = EXAM_CONFIG.get(exam_slug)
    allowed_langs = cfg["allowed_languages"] if cfg else ["ta"]

    return PastYearPaperOut(
        id=paper.id,
        exam_id=paper.exam_id,
        year=paper.year,
        title=paper.title,
        description=paper.description,
        duration_minutes=paper.duration_minutes,
        question_count=paper.question_count,
        marks_per_question=paper.marks_per_question,
        negative_mark=paper.negative_mark,
        price=paper.price,
        status=paper.status,
        exam_name=exam_name,
        exam_slug=exam_slug,
        allowed_languages=allowed_langs,
        created_at=paper.created_at,
        updated_at=paper.updated_at
    )

@router.delete("/{paper_id}")
def delete_past_year_paper(
    paper_id: int,
    db = Depends(get_db),
    admin = Depends(get_admin_user)
):
    paper_doc = db.past_year_papers.find_one({"id": paper_id})
    if not paper_doc:
        raise HTTPException(status_code=404, detail="Past year paper not found")

    db.questions.delete_many({"past_year_paper_id": paper_id})
    db.past_year_papers.delete_one({"id": paper_id})

    return {"message": f"Past Year Paper {paper_id} deleted successfully."}

@router.post("/{paper_id}/questions")
def add_question_to_past_year_paper(
    paper_id: int,
    req: QuestionCreate,
    db = Depends(get_db),
    admin = Depends(get_admin_user)
):
    paper_doc = db.past_year_papers.find_one({"id": paper_id})
    if not paper_doc:
        raise HTTPException(status_code=404, detail="Past year paper not found")

    q_id = get_next_sequence(db, "question_id")
    now = datetime.utcnow()
    q_doc = {
        "id": q_id,
        "test_id": None,
        "question_set_id": None,
        "past_year_paper_id": paper_id,
        "question_group_id": req.question_group_id,
        "language": req.language,
        "question_text": req.question_text,
        "option_a": req.option_a,
        "option_b": req.option_b,
        "option_c": req.option_c,
        "option_d": req.option_d,
        "correct_option": req.correct_option.upper(),
        "explanation": req.explanation,
        "question_order": req.question_order,
        "source": req.source if hasattr(req, 'source') else "MANUAL",
        "question_source": getattr(req, 'question_source', "ORIGINAL"),
        "status": getattr(req, 'status', "ACTIVE"),
        "created_at": now,
        "updated_at": now
    }
    db.questions.insert_one(q_doc)

    groups = db.questions.distinct("question_group_id", {"past_year_paper_id": paper_id})
    db.past_year_papers.update_one({"id": paper_id}, {"$set": {"question_count": len(groups)}})

    return QuestionFullOut.model_validate(q_doc)

@router.post("/{paper_id}/questions/group2")
def add_group2_question_to_past_year_paper(
    paper_id: int,
    req: Group2QuestionCreate,
    db = Depends(get_db),
    admin = Depends(get_admin_user)
):
    paper_doc = db.past_year_papers.find_one({"id": paper_id})
    if not paper_doc:
        raise HTTPException(status_code=404, detail="Past year paper not found")

    next_grp_id = get_next_sequence(db, "question_group_id")
    now = datetime.utcnow()

    q_ta_id = get_next_sequence(db, "question_id")
    q_ta_doc = {
        "id": q_ta_id,
        "test_id": None,
        "question_set_id": None,
        "past_year_paper_id": paper_id,
        "question_group_id": next_grp_id,
        "language": "ta",
        "question_text": req.question_text_ta,
        "option_a": req.option_a_ta,
        "option_b": req.option_b_ta,
        "option_c": req.option_c_ta,
        "option_d": req.option_d_ta,
        "correct_option": req.correct_option_ta.upper(),
        "explanation": req.explanation_ta,
        "question_order": req.question_order,
        "source": "MANUAL",
        "question_source": getattr(req, 'question_source', "ORIGINAL"),
        "status": "ACTIVE",
        "created_at": now,
        "updated_at": now
    }

    q_en_id = get_next_sequence(db, "question_id")
    q_en_doc = {
        "id": q_en_id,
        "test_id": None,
        "question_set_id": None,
        "past_year_paper_id": paper_id,
        "question_group_id": next_grp_id,
        "language": "en",
        "question_text": req.question_text_en,
        "option_a": req.option_a_en,
        "option_b": req.option_b_en,
        "option_c": req.option_c_en,
        "option_d": req.option_d_en,
        "correct_option": req.correct_option_en.upper(),
        "explanation": req.explanation_en,
        "question_order": req.question_order,
        "source": "MANUAL",
        "question_source": getattr(req, 'question_source', "ORIGINAL"),
        "status": "ACTIVE",
        "created_at": now,
        "updated_at": now
    }

    db.questions.insert_one(q_ta_doc)
    db.questions.insert_one(q_en_doc)

    groups = db.questions.distinct("question_group_id", {"past_year_paper_id": paper_id})
    db.past_year_papers.update_one({"id": paper_id}, {"$set": {"question_count": len(groups)}})

    return {"message": "Dual-language questions added successfully", "question_group_id": next_grp_id}

@router.post("/{paper_id}/upload-pdf")
async def upload_pdf_for_past_year_paper(
    paper_id: int,
    file: UploadFile = File(...),
    db = Depends(get_db),
    admin = Depends(get_admin_user)
):
    paper_doc = db.past_year_papers.find_one({"id": paper_id})
    if not paper_doc:
        raise HTTPException(status_code=404, detail="Past year paper not found")
    paper = to_mongo_doc(paper_doc)

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    contents = await file.read()
    raw_text = extract_text_from_pdf_bytes(contents)

    exam_doc = db.exams.find_one({"id": paper.exam_id}) if paper.exam_id else None
    exam_slug = exam_doc["slug"] if exam_doc else "tnpsc-group-4"
    parsed_questions = parse_pdf_questions(raw_text, exam_slug)

    added_count = 0
    now = datetime.utcnow()

    for idx, pq in enumerate(parsed_questions, start=1):
        grp_id = get_next_sequence(db, "question_group_id")
        if exam_slug == "tnpsc-group-2":
            q_ta_id = get_next_sequence(db, "question_id")
            q_ta_doc = {
                "id": q_ta_id,
                "test_id": None,
                "question_set_id": None,
                "past_year_paper_id": paper.id,
                "question_group_id": grp_id,
                "language": "ta",
                "question_text": pq["question_text"],
                "option_a": pq["option_a"],
                "option_b": pq["option_b"],
                "option_c": pq["option_c"],
                "option_d": pq["option_d"],
                "correct_option": pq["correct_option"].upper(),
                "explanation": pq.get("explanation", ""),
                "question_order": idx,
                "source": "PDF",
                "question_source": "ORIGINAL",
                "status": "ACTIVE",
                "created_at": now,
                "updated_at": now
            }
            q_en_id = get_next_sequence(db, "question_id")
            q_en_doc = {
                "id": q_en_id,
                "test_id": None,
                "question_set_id": None,
                "past_year_paper_id": paper.id,
                "question_group_id": grp_id,
                "language": "en",
                "question_text": f"[ENG] {pq['question_text']}",
                "option_a": f"[ENG] {pq['option_a']}",
                "option_b": f"[ENG] {pq['option_b']}",
                "option_c": f"[ENG] {pq['option_c']}",
                "option_d": f"[ENG] {pq['option_d']}",
                "correct_option": pq["correct_option"].upper(),
                "explanation": f"[ENG] {pq.get('explanation', '')}",
                "question_order": idx,
                "source": "PDF",
                "question_source": "ORIGINAL",
                "status": "ACTIVE",
                "created_at": now,
                "updated_at": now
            }
            db.questions.insert_one(q_ta_doc)
            db.questions.insert_one(q_en_doc)
        else:
            q_ta_id = get_next_sequence(db, "question_id")
            q_ta_doc = {
                "id": q_ta_id,
                "test_id": None,
                "question_set_id": None,
                "past_year_paper_id": paper.id,
                "question_group_id": grp_id,
                "language": "ta",
                "question_text": pq["question_text"],
                "option_a": pq["option_a"],
                "option_b": pq["option_b"],
                "option_c": pq["option_c"],
                "option_d": pq["option_d"],
                "correct_option": pq["correct_option"].upper(),
                "explanation": pq.get("explanation", ""),
                "question_order": idx,
                "source": "PDF",
                "question_source": "ORIGINAL",
                "status": "ACTIVE",
                "created_at": now,
                "updated_at": now
            }
            db.questions.insert_one(q_ta_doc)
        added_count += 1

    db.past_year_papers.update_one(
        {"id": paper.id},
        {"$set": {
            "status": PastYearPaperStatus.REVIEW,
            "question_count": added_count,
            "updated_at": now
        }}
    )

    log_id = get_next_sequence(db, "audit_log_id")
    db.audit_logs.insert_one({
        "id": log_id,
        "user_id": admin.id,
        "action": "UPLOAD_PAST_YEAR_PDF",
        "past_year_paper_id": paper.id,
        "details": f"Uploaded PDF '{file.filename}', parsed {added_count} questions. Status moved to REVIEW.",
        "created_at": now
    })

    return {
        "message": f"Successfully extracted {added_count} questions from PDF.",
        "status": PastYearPaperStatus.REVIEW,
        "question_count": added_count
    }

@router.post("/{paper_id}/grant-access")
def grant_access_to_past_year_paper(
    paper_id: int,
    req: AdminGrantAccessRequest,
    db = Depends(get_db),
    admin = Depends(get_admin_user)
):
    paper_doc = db.past_year_papers.find_one({"id": paper_id})
    if not paper_doc:
        raise HTTPException(status_code=404, detail="Past year paper not found")
    paper = to_mongo_doc(paper_doc)

    target_user_doc = db.users.find_one({"$or": [{"email": req.user_id_or_email.lower()}, {"mobile": req.user_id_or_email}]})
    if not target_user_doc and req.user_id_or_email.isdigit():
        target_user_doc = db.users.find_one({"id": int(req.user_id_or_email)})

    if not target_user_doc:
        raise HTTPException(status_code=404, detail=f"Student '{req.user_id_or_email}' not found")
    target_user = to_mongo_doc(target_user_doc)

    existing = db.payments.find_one({
        "user_id": target_user.id,
        "past_year_paper_id": paper.id,
        "status": PaymentStatus.SUCCESS
    })

    if existing:
        return {"message": f"Student '{target_user.name}' already has access to this past year paper."}

    payment_id = get_next_sequence(db, "payment_id")
    now = datetime.utcnow()
    db.payments.insert_one({
        "id": payment_id,
        "user_id": target_user.id,
        "test_id": None,
        "past_year_paper_id": paper.id,
        "amount": 0.0,
        "gateway_order_id": f"ADMIN_GRANT_{paper.id}_{target_user.id}",
        "gateway_payment_id": f"GRANT_PAY_{paper.id}_{target_user.id}",
        "status": PaymentStatus.SUCCESS,
        "payment_method": PaymentMethod.ADMIN_GRANTED,
        "created_at": now
    })

    log_id = get_next_sequence(db, "audit_log_id")
    db.audit_logs.insert_one({
        "id": log_id,
        "user_id": admin.id,
        "action": "GRANT_PAST_YEAR_ACCESS",
        "past_year_paper_id": paper.id,
        "details": f"Admin Granted Access for Past Year Paper {paper.title} to student {target_user.email}",
        "created_at": now
    })

    return {"message": f"Granted free access for '{paper.title}' to {target_user.name} ({target_user.email})"}
