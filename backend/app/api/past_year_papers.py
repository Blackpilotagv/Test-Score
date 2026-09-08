from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database.session import get_db
from app.models.models import (
    User, Exam, PastYearPaper, PastYearPaperStatus, Question,
    Payment, PaymentStatus, TestAttempt, AttemptStatus, Answer
)
from app.schemas.schemas import (
    PastYearPaperOut, StartAttemptRequest, SaveAnswerRequest,
    QuestionClientOut, QuestionReviewOut, ResultOut, AttemptSummaryOut
)
from app.api.deps import get_current_user
from app.services.eval_service import evaluate_attempt, check_and_get_remaining_seconds
from app.core.config import EXAM_CONFIG

router = APIRouter(prefix="/past-year-papers", tags=["Student Past Year Papers"])

@router.get("", response_model=List[PastYearPaperOut])
def get_published_past_year_papers(
    exam_id: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    query = db.query(PastYearPaper).filter(PastYearPaper.status == PastYearPaperStatus.PUBLISHED)
    if exam_id:
        query = query.filter(PastYearPaper.exam_id == exam_id)
    if year:
        query = query.filter(PastYearPaper.year == year)

    papers = query.order_by(PastYearPaper.year.desc(), PastYearPaper.id.desc()).all()

    # User payments check
    purchased_paper_ids = set()
    if current_user:
        payments = db.query(Payment.past_year_paper_id).filter(
            Payment.user_id == current_user.id,
            Payment.status == PaymentStatus.SUCCESS,
            Payment.past_year_paper_id != None
        ).all()
        purchased_paper_ids = {p[0] for p in payments}

    out = []
    for p in papers:
        cfg = EXAM_CONFIG.get(p.exam.slug) if p.exam else None
        allowed_langs = cfg["allowed_languages"] if cfg else ["ta"]
        has_access = (p.price == 0.0) or (p.id in purchased_paper_ids)

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
            updated_at=p.updated_at,
            has_access=has_access
        ))
    return out

@router.get("/{paper_id}", response_model=PastYearPaperOut)
def get_past_year_paper_by_id(
    paper_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    paper = db.query(PastYearPaper).filter(PastYearPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Past year paper not found")

    has_access = False
    if paper.price == 0.0:
        has_access = True
    elif current_user:
        pmt = db.query(Payment).filter(
            Payment.user_id == current_user.id,
            Payment.past_year_paper_id == paper.id,
            Payment.status == PaymentStatus.SUCCESS
        ).first()
        if pmt:
            has_access = True

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
        updated_at=paper.updated_at,
        has_access=has_access
    )

@router.post("/{paper_id}/start")
def start_past_year_attempt(
    paper_id: int,
    req: StartAttemptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    paper = db.query(PastYearPaper).filter(PastYearPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Past year paper not found")

    if paper.status != PastYearPaperStatus.PUBLISHED:
        raise HTTPException(status_code=400, detail="This past year paper is not currently available.")

    # Access control
    if paper.price > 0:
        pmt = db.query(Payment).filter(
            Payment.user_id == current_user.id,
            Payment.past_year_paper_id == paper.id,
            Payment.status == PaymentStatus.SUCCESS
        ).first()
        if not pmt:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You must purchase this paper before attempting.")

    cfg = EXAM_CONFIG.get(paper.exam.slug) if paper.exam else None
    allowed_langs = cfg["allowed_languages"] if cfg else ["ta"]

    if req.language not in allowed_langs:
        raise HTTPException(status_code=400, detail=f"Language '{req.language}' not allowed for this paper.")

    # Check existing attempt
    attempt = db.query(TestAttempt).filter(
        TestAttempt.user_id == current_user.id,
        TestAttempt.past_year_paper_id == paper.id
    ).order_by(TestAttempt.id.desc()).first()

    if not attempt or attempt.status == AttemptStatus.SUBMITTED:
        unique_groups = db.query(Question.question_group_id).filter(
            Question.past_year_paper_id == paper.id
        ).distinct().count()

        attempt = TestAttempt(
            user_id=current_user.id,
            past_year_paper_id=paper.id,
            started_at=datetime.utcnow(),
            status=AttemptStatus.IN_PROGRESS,
            total_questions=unique_groups
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)

    remaining_secs = check_and_get_remaining_seconds(attempt, paper.duration_minutes)
    if remaining_secs <= 0 and attempt.status == AttemptStatus.IN_PROGRESS:
        evaluate_attempt(db, attempt.id)
        raise HTTPException(status_code=400, detail="Paper attempt timer has expired.")

    questions = db.query(Question).filter(
        Question.past_year_paper_id == paper.id,
        Question.language == req.language
    ).order_by(Question.question_order.asc()).all()

    q_out = [QuestionClientOut.model_validate(q) for q in questions]

    user_answers = db.query(Answer).filter(Answer.attempt_id == attempt.id).all()
    answers_dict = {ans.question_group_id: ans.selected_option for ans in user_answers}

    return {
        "attempt_id": attempt.id,
        "past_year_paper_id": paper.id,
        "test_title": paper.title,
        "exam_name": paper.exam.name if paper.exam else "",
        "duration_minutes": paper.duration_minutes,
        "remaining_seconds": remaining_secs,
        "status": attempt.status.value,
        "allowed_languages": allowed_langs,
        "current_language": req.language,
        "questions": q_out,
        "saved_answers": answers_dict
    }

@router.get("/attempts/{attempt_id}")
def get_paper_attempt_status(
    attempt_id: int,
    language: str = "ta",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    attempt = db.query(TestAttempt).filter(
        TestAttempt.id == attempt_id,
        TestAttempt.user_id == current_user.id
    ).first()
    if not attempt or not attempt.past_year_paper_id:
        raise HTTPException(status_code=404, detail="Paper attempt not found")

    paper = attempt.past_year_paper
    cfg = EXAM_CONFIG.get(paper.exam.slug) if paper.exam else None
    allowed_langs = cfg["allowed_languages"] if cfg else ["ta"]

    remaining_secs = check_and_get_remaining_seconds(attempt, paper.duration_minutes)
    if remaining_secs <= 0 and attempt.status == AttemptStatus.IN_PROGRESS:
        attempt = evaluate_attempt(db, attempt.id)

    questions = db.query(Question).filter(
        Question.past_year_paper_id == paper.id,
        Question.language == language
    ).order_by(Question.question_order.asc()).all()

    q_out = [QuestionClientOut.model_validate(q) for q in questions]
    user_answers = db.query(Answer).filter(Answer.attempt_id == attempt.id).all()
    answers_dict = {ans.question_group_id: ans.selected_option for ans in user_answers}

    return {
        "attempt_id": attempt.id,
        "past_year_paper_id": paper.id,
        "test_title": paper.title,
        "exam_name": paper.exam.name if paper.exam else "",
        "duration_minutes": paper.duration_minutes,
        "remaining_seconds": remaining_secs,
        "status": attempt.status.value,
        "allowed_languages": allowed_langs,
        "current_language": language,
        "questions": q_out,
        "saved_answers": answers_dict
    }

@router.post("/attempts/{attempt_id}/answer")
def auto_save_paper_answer(
    attempt_id: int,
    req: SaveAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    attempt = db.query(TestAttempt).filter(
        TestAttempt.id == attempt_id,
        TestAttempt.user_id == current_user.id
    ).first()
    if not attempt or not attempt.past_year_paper_id:
        raise HTTPException(status_code=404, detail="Paper attempt not found")

    if attempt.status != AttemptStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Attempt is already completed or expired")

    paper = attempt.past_year_paper
    if check_and_get_remaining_seconds(attempt, paper.duration_minutes) <= 0:
        evaluate_attempt(db, attempt.id)
        raise HTTPException(status_code=400, detail="Timer expired. Paper attempt submitted automatically.")

    ans = db.query(Answer).filter(
        Answer.attempt_id == attempt.id,
        Answer.question_group_id == req.question_group_id
    ).first()

    if not ans:
        ans = Answer(
            attempt_id=attempt.id,
            question_group_id=req.question_group_id,
            selected_option=req.selected_option,
            answered_at=datetime.utcnow()
        )
        db.add(ans)
    else:
        ans.selected_option = req.selected_option
        ans.answered_at = datetime.utcnow()

    db.commit()
    return {"status": "saved", "question_group_id": req.question_group_id, "selected_option": req.selected_option}

@router.post("/attempts/{attempt_id}/submit")
def submit_paper_attempt(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    attempt = db.query(TestAttempt).filter(
        TestAttempt.id == attempt_id,
        TestAttempt.user_id == current_user.id
    ).first()
    if not attempt or not attempt.past_year_paper_id:
        raise HTTPException(status_code=404, detail="Paper attempt not found")

    evaluated = evaluate_attempt(db, attempt.id)
    return {
        "attempt_id": evaluated.id,
        "past_year_paper_id": evaluated.past_year_paper_id,
        "score": evaluated.score,
        "percentage": evaluated.percentage,
        "correct_answers": evaluated.correct_answers,
        "wrong_answers": evaluated.wrong_answers,
        "unanswered": evaluated.unanswered,
        "total_questions": evaluated.total_questions,
        "time_taken": evaluated.time_taken,
        "status": evaluated.status.value
    }

@router.get("/attempts/{attempt_id}/result", response_model=ResultOut)
def get_paper_attempt_result(
    attempt_id: int,
    language: str = "ta",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    attempt = db.query(TestAttempt).filter(
        TestAttempt.id == attempt_id,
        TestAttempt.user_id == current_user.id
    ).first()
    if not attempt or not attempt.past_year_paper_id:
        raise HTTPException(status_code=404, detail="Paper attempt not found")

    if attempt.status != AttemptStatus.SUBMITTED:
        attempt = evaluate_attempt(db, attempt.id)

    paper = attempt.past_year_paper
    cfg = EXAM_CONFIG.get(paper.exam.slug) if paper.exam else None
    allowed_langs = cfg["allowed_languages"] if cfg else ["ta"]

    questions = db.query(Question).filter(
        Question.past_year_paper_id == paper.id,
        Question.language == language
    ).order_by(Question.question_order.asc()).all()

    user_answers = db.query(Answer).filter(Answer.attempt_id == attempt.id).all()
    answers_map = {ans.question_group_id: ans for ans in user_answers}

    reviews = []
    for q in questions:
        ans = answers_map.get(q.question_group_id)
        stud_ans = ans.selected_option if ans else None
        if not stud_ans:
            st = "Unanswered"
        elif stud_ans.upper() == q.correct_option.upper():
            st = "Correct"
        else:
            st = "Incorrect"

        reviews.append(QuestionReviewOut(
            question_group_id=q.question_group_id,
            question_order=q.question_order,
            language=q.language,
            question_text=q.question_text,
            option_a=q.option_a,
            option_b=q.option_b,
            option_c=q.option_c,
            option_d=q.option_d,
            student_answer=stud_ans,
            correct_answer=q.correct_option,
            status=st,
            explanation=q.explanation
        ))

    return ResultOut(
        attempt_id=attempt.id,
        test_id=None,
        past_year_paper_id=paper.id,
        test_title=paper.title,
        exam_name=paper.exam.name if paper.exam else "",
        allowed_languages=allowed_langs,
        active_language=language,
        started_at=attempt.started_at,
        submitted_at=attempt.submitted_at,
        score=attempt.score,
        percentage=attempt.percentage,
        correct_answers=attempt.correct_answers,
        wrong_answers=attempt.wrong_answers,
        unanswered=attempt.unanswered,
        total_questions=attempt.total_questions,
        time_taken=attempt.time_taken,
        questions_review=reviews
    )
