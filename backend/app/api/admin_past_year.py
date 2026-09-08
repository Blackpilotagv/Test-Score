from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database.session import get_db
from app.models.models import User, Exam, PastYearPaper, PastYearPaperStatus, Question, Payment, PaymentStatus, PaymentMethod, AuditLog
from app.schemas.schemas import (
    PastYearPaperCreate, PastYearPaperUpdate, PastYearPaperOut,
    QuestionBase, QuestionCreate, Group2QuestionCreate, QuestionUpdate, QuestionFullOut,
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
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    query = db.query(PastYearPaper)
    if exam_id:
        query = query.filter(PastYearPaper.exam_id == exam_id)
    if year:
        query = query.filter(PastYearPaper.year == year)
    if paper_status:
        query = query.filter(PastYearPaper.status == paper_status)

    papers = query.order_by(PastYearPaper.year.desc(), PastYearPaper.id.desc()).all()
    out = []
    for p in papers:
        cfg = EXAM_CONFIG.get(p.exam.slug) if p.exam else None
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
            exam_name=p.exam.name if p.exam else "",
            exam_slug=p.exam.slug if p.exam else "",
            allowed_languages=allowed_langs,
            created_at=p.created_at,
            updated_at=p.updated_at
        ))
    return out

@router.post("", response_model=PastYearPaperOut)
def create_past_year_paper(
    req: PastYearPaperCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    exam = db.query(Exam).filter(Exam.id == req.exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam category not found")

    paper = PastYearPaper(
        exam_id=req.exam_id,
        year=req.year,
        title=req.title,
        description=req.description,
        duration_minutes=req.duration_minutes,
        question_count=req.question_count,
        marks_per_question=req.marks_per_question,
        negative_mark=req.negative_mark,
        price=req.price,
        status=req.status,
        created_by=admin.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)

    # Audit log
    audit = AuditLog(
        user_id=admin.id,
        action="CREATE_PAST_YEAR_PAPER",
        past_year_paper_id=paper.id,
        details=f"Created Past Year Paper '{paper.title}' for {exam.name} ({paper.year})"
    )
    db.add(audit)
    db.commit()

    cfg = EXAM_CONFIG.get(exam.slug)
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
        exam_name=exam.name,
        exam_slug=exam.slug,
        allowed_languages=allowed_langs,
        created_at=paper.created_at,
        updated_at=paper.updated_at
    )

@router.get("/{paper_id}")
def get_past_year_paper_details(
    paper_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    paper = db.query(PastYearPaper).filter(PastYearPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Past year paper not found")

    questions = db.query(Question).filter(
        Question.past_year_paper_id == paper.id
    ).order_by(Question.question_order.asc(), Question.language.asc()).all()

    cfg = EXAM_CONFIG.get(paper.exam.slug) if paper.exam else None
    allowed_langs = cfg["allowed_languages"] if cfg else ["ta"]

    q_outs = [QuestionFullOut.model_validate(q) for q in questions]

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
            exam_name=paper.exam.name if paper.exam else "",
            exam_slug=paper.exam.slug if paper.exam else "",
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
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    paper = db.query(PastYearPaper).filter(PastYearPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Past year paper not found")

    if req.exam_id is not None:
        paper.exam_id = req.exam_id
    if req.year is not None:
        paper.year = req.year
    if req.title is not None:
        paper.title = req.title
    if req.description is not None:
        paper.description = req.description
    if req.duration_minutes is not None:
        paper.duration_minutes = req.duration_minutes
    if req.question_count is not None:
        paper.question_count = req.question_count
    if req.marks_per_question is not None:
        paper.marks_per_question = req.marks_per_question
    if req.negative_mark is not None:
        paper.negative_mark = req.negative_mark
    if req.price is not None:
        paper.price = req.price
    if req.status is not None:
        paper.status = req.status

    paper.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(paper)

    # Audit log
    audit = AuditLog(
        user_id=admin.id,
        action="UPDATE_PAST_YEAR_PAPER",
        past_year_paper_id=paper.id,
        details=f"Updated Past Year Paper status/metadata to {paper.status}"
    )
    db.add(audit)
    db.commit()

    cfg = EXAM_CONFIG.get(paper.exam.slug) if paper.exam else None
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
        exam_name=paper.exam.name if paper.exam else "",
        exam_slug=paper.exam.slug if paper.exam else "",
        allowed_languages=allowed_langs,
        created_at=paper.created_at,
        updated_at=paper.updated_at
    )

@router.delete("/{paper_id}")
def delete_past_year_paper(
    paper_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    paper = db.query(PastYearPaper).filter(PastYearPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Past year paper not found")

    db.delete(paper)
    db.commit()

    return {"message": f"Past Year Paper {paper_id} deleted successfully."}

@router.post("/{paper_id}/questions")
def add_question_to_past_year_paper(
    paper_id: int,
    req: QuestionCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    paper = db.query(PastYearPaper).filter(PastYearPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Past year paper not found")

    q = Question(
        past_year_paper_id=paper.id,
        question_group_id=req.question_group_id,
        language=req.language,
        question_text=req.question_text,
        option_a=req.option_a,
        option_b=req.option_b,
        option_c=req.option_c,
        option_d=req.option_d,
        correct_option=req.correct_option.upper(),
        explanation=req.explanation,
        question_order=req.question_order,
        source=req.source,
        question_source=req.question_source,
        status=req.status
    )
    db.add(q)

    # Update paper question count
    unique_count = db.query(Question.question_group_id).filter(Question.past_year_paper_id == paper.id).distinct().count()
    paper.question_count = unique_count
    db.commit()
    db.refresh(q)

    return QuestionFullOut.model_validate(q)

@router.post("/{paper_id}/questions/group2")
def add_group2_question_to_past_year_paper(
    paper_id: int,
    req: Group2QuestionCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    paper = db.query(PastYearPaper).filter(PastYearPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Past year paper not found")

    # Generate next question_group_id
    max_grp = db.query(Question.question_group_id).order_by(Question.question_group_id.desc()).first()
    next_grp_id = (max_grp[0] + 1) if max_grp else 1001

    q_ta = Question(
        past_year_paper_id=paper.id,
        question_group_id=next_grp_id,
        language="ta",
        question_text=req.question_text_ta,
        option_a=req.option_a_ta,
        option_b=req.option_b_ta,
        option_c=req.option_c_ta,
        option_d=req.option_d_ta,
        correct_option=req.correct_option_ta.upper(),
        explanation=req.explanation_ta,
        question_order=req.question_order,
        source="MANUAL",
        question_source=req.question_source
    )
    q_en = Question(
        past_year_paper_id=paper.id,
        question_group_id=next_grp_id,
        language="en",
        question_text=req.question_text_en,
        option_a=req.option_a_en,
        option_b=req.option_b_en,
        option_c=req.option_c_en,
        option_d=req.option_d_en,
        correct_option=req.correct_option_en.upper(),
        explanation=req.explanation_en,
        question_order=req.question_order,
        source="MANUAL",
        question_source=req.question_source
    )
    db.add(q_ta)
    db.add(q_en)

    unique_count = db.query(Question.question_group_id).filter(Question.past_year_paper_id == paper.id).distinct().count() + 1
    paper.question_count = unique_count
    db.commit()

    return {"message": "Dual-language questions added successfully", "question_group_id": next_grp_id}

@router.post("/{paper_id}/upload-pdf")
async def upload_pdf_for_past_year_paper(
    paper_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    paper = db.query(PastYearPaper).filter(PastYearPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Past year paper not found")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    contents = await file.read()
    raw_text = extract_text_from_pdf_bytes(contents)
    exam_slug = paper.exam.slug if paper.exam else "tnpsc-group-4"
    parsed_questions = parse_pdf_questions(raw_text, exam_slug)

    # Get max group ID
    max_grp = db.query(Question.question_group_id).order_by(Question.question_group_id.desc()).first()
    base_grp_id = (max_grp[0] + 1) if max_grp else 1000

    added_count = 0
    for idx, pq in enumerate(parsed_questions, start=1):
        grp_id = base_grp_id + idx
        if exam_slug == "group2":
            q_ta = Question(
                past_year_paper_id=paper.id,
                question_group_id=grp_id,
                language="ta",
                question_text=pq["question_text"],
                option_a=pq["option_a"],
                option_b=pq["option_b"],
                option_c=pq["option_c"],
                option_d=pq["option_d"],
                correct_option=pq["correct_option"].upper(),
                explanation=pq.get("explanation", ""),
                question_order=idx,
                source="PDF",
                question_source="ORIGINAL"
            )
            q_en = Question(
                past_year_paper_id=paper.id,
                question_group_id=grp_id,
                language="en",
                question_text=f"[ENG] {pq['question_text']}",
                option_a=f"[ENG] {pq['option_a']}",
                option_b=f"[ENG] {pq['option_b']}",
                option_c=f"[ENG] {pq['option_c']}",
                option_d=f"[ENG] {pq['option_d']}",
                correct_option=pq["correct_option"].upper(),
                explanation=f"[ENG] {pq.get('explanation', '')}",
                question_order=idx,
                source="PDF",
                question_source="ORIGINAL"
            )
            db.add(q_ta)
            db.add(q_en)
        else:
            q_ta = Question(
                past_year_paper_id=paper.id,
                question_group_id=grp_id,
                language="ta",
                question_text=pq["question_text"],
                option_a=pq["option_a"],
                option_b=pq["option_b"],
                option_c=pq["option_c"],
                option_d=pq["option_d"],
                correct_option=pq["correct_option"].upper(),
                explanation=pq.get("explanation", ""),
                question_order=idx,
                source="PDF",
                question_source="ORIGINAL"
            )
            db.add(q_ta)
        added_count += 1

    paper.status = PastYearPaperStatus.REVIEW
    paper.question_count = added_count
    paper.updated_at = datetime.utcnow()

    # Audit log
    audit = AuditLog(
        user_id=admin.id,
        action="UPLOAD_PAST_YEAR_PDF",
        past_year_paper_id=paper.id,
        details=f"Uploaded PDF '{file.filename}', parsed {added_count} questions. Status moved to REVIEW."
    )
    db.add(audit)
    db.commit()

    return {
        "message": f"Successfully extracted {added_count} questions from PDF.",
        "status": paper.status.value,
        "question_count": added_count
    }

@router.post("/{paper_id}/grant-access")
def grant_access_to_past_year_paper(
    paper_id: int,
    req: AdminGrantAccessRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    paper = db.query(PastYearPaper).filter(PastYearPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Past year paper not found")

    target_user = db.query(User).filter(
        (User.email == req.user_id_or_email) | (User.mobile == req.user_id_or_email)
    ).first()
    if not target_user and req.user_id_or_email.isdigit():
        target_user = db.query(User).filter(User.id == int(req.user_id_or_email)).first()

    if not target_user:
        raise HTTPException(status_code=404, detail=f"Student '{req.user_id_or_email}' not found")

    existing = db.query(Payment).filter(
        Payment.user_id == target_user.id,
        Payment.past_year_paper_id == paper.id,
        Payment.status == PaymentStatus.SUCCESS
    ).first()

    if existing:
        return {"message": f"Student '{target_user.name}' already has access to this past year paper."}

    payment = Payment(
        user_id=target_user.id,
        past_year_paper_id=paper.id,
        amount=0.0,
        gateway_order_id=f"ADMIN_GRANT_{paper.id}_{target_user.id}",
        gateway_payment_id=f"GRANT_PAY_{paper.id}_{target_user.id}",
        status=PaymentStatus.SUCCESS,
        payment_method=PaymentMethod.ADMIN_GRANTED
    )
    db.add(payment)

    # Audit log
    audit = AuditLog(
        user_id=admin.id,
        action="GRANT_PAST_YEAR_ACCESS",
        past_year_paper_id=paper.id,
        details=f"Admin Granted Access for Past Year Paper {paper.title} to student {target_user.email}"
    )
    db.add(audit)
    db.commit()

    return {"message": f"Granted free access for '{paper.title}' to {target_user.name} ({target_user.email})"}
