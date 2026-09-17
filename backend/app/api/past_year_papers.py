from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo import DESCENDING, ASCENDING

from app.database.session import get_db, get_next_sequence
from app.models.models import (
    PastYearPaperStatus, PaymentStatus, AttemptStatus, to_mongo_doc
)
from app.schemas.schemas import (
    PastYearPaperOut, StartAttemptRequest, SaveAnswerRequest,
    QuestionClientOut, QuestionReviewOut, ResultOut
)
from app.api.deps import get_current_user
from app.services.eval_service import evaluate_attempt, check_and_get_remaining_seconds
from app.core.config import EXAM_CONFIG

router = APIRouter(prefix="/past-year-papers", tags=["Student Past Year Papers"])

@router.get("", response_model=List[PastYearPaperOut])
def get_published_past_year_papers(
    exam_id: Optional[int] = None,
    year: Optional[int] = None,
    db = Depends(get_db),
    current_user: Optional[Any] = Depends(get_current_user)
):
    query_filter = {"status": PastYearPaperStatus.PUBLISHED}
    if exam_id:
        query_filter["exam_id"] = exam_id
    if year:
        query_filter["year"] = year

    paper_docs = list(db.past_year_papers.find(
        query_filter,
        sort=[("year", DESCENDING), ("id", DESCENDING)]
    ))

    purchased_paper_ids = set()
    if current_user:
        pmts = list(db.payments.find({
            "user_id": current_user.id,
            "status": PaymentStatus.SUCCESS,
            "past_year_paper_id": {"$ne": None}
        }))
        purchased_paper_ids = {p["past_year_paper_id"] for p in pmts if p.get("past_year_paper_id")}

    out = []
    for p_doc in paper_docs:
        p = to_mongo_doc(p_doc)
        exam_doc = db.exams.find_one({"id": p.exam_id}) if p.exam_id else None
        exam_name = exam_doc["name"] if exam_doc else ""
        exam_slug = exam_doc["slug"] if exam_doc else ""
        cfg = EXAM_CONFIG.get(exam_slug)
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
            exam_name=exam_name,
            exam_slug=exam_slug,
            allowed_languages=allowed_langs,
            created_at=p.created_at,
            updated_at=p.updated_at,
            has_access=has_access
        ))
    return out

@router.get("/{paper_id}", response_model=PastYearPaperOut)
def get_past_year_paper_by_id(
    paper_id: int,
    db = Depends(get_db),
    current_user: Optional[Any] = Depends(get_current_user)
):
    paper_doc = db.past_year_papers.find_one({"id": paper_id})
    if not paper_doc:
        raise HTTPException(status_code=404, detail="Past year paper not found")

    paper = to_mongo_doc(paper_doc)
    has_access = False
    if paper.price == 0.0:
        has_access = True
    elif current_user:
        pmt = db.payments.find_one({
            "user_id": current_user.id,
            "past_year_paper_id": paper.id,
            "status": PaymentStatus.SUCCESS
        })
        if pmt:
            has_access = True

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
        updated_at=paper.updated_at,
        has_access=has_access
    )

@router.post("/{paper_id}/start")
def start_past_year_attempt(
    paper_id: int,
    req: StartAttemptRequest,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    paper_doc = db.past_year_papers.find_one({"id": paper_id})
    if not paper_doc:
        raise HTTPException(status_code=404, detail="Past year paper not found")
    paper = to_mongo_doc(paper_doc)

    if paper.status != PastYearPaperStatus.PUBLISHED:
        raise HTTPException(status_code=400, detail="This past year paper is not currently available.")

    if paper.price > 0:
        pmt = db.payments.find_one({
            "user_id": current_user.id,
            "past_year_paper_id": paper.id,
            "status": PaymentStatus.SUCCESS
        })
        if not pmt:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You must purchase this paper before attempting.")

    exam_doc = db.exams.find_one({"id": paper.exam_id}) if paper.exam_id else None
    exam_name = exam_doc["name"] if exam_doc else ""
    exam_slug = exam_doc["slug"] if exam_doc else ""
    cfg = EXAM_CONFIG.get(exam_slug)
    allowed_langs = cfg["allowed_languages"] if cfg else ["ta"]

    if req.language not in allowed_langs:
        raise HTTPException(status_code=400, detail=f"Language '{req.language}' not allowed for this paper.")

    attempt_doc = db.test_attempts.find_one(
        {"user_id": current_user.id, "past_year_paper_id": paper.id},
        sort=[("id", DESCENDING)]
    )
    attempt = to_mongo_doc(attempt_doc)

    if not attempt or attempt.status == AttemptStatus.SUBMITTED:
        groups = db.questions.distinct("question_group_id", {"past_year_paper_id": paper.id})
        unique_groups = len(groups)

        attempt_id = get_next_sequence(db, "attempt_id")
        now = datetime.utcnow()
        new_attempt = {
            "id": attempt_id,
            "user_id": current_user.id,
            "test_id": None,
            "question_set_id": None,
            "past_year_paper_id": paper.id,
            "started_at": now,
            "submitted_at": None,
            "status": AttemptStatus.IN_PROGRESS,
            "score": 0.0,
            "correct_answers": 0,
            "wrong_answers": 0,
            "unanswered": 0,
            "total_questions": unique_groups,
            "percentage": 0.0,
            "time_taken": None,
            "created_at": now
        }
        db.test_attempts.insert_one(new_attempt)
        attempt = to_mongo_doc(new_attempt)

    remaining_secs = check_and_get_remaining_seconds(attempt, paper.duration_minutes)
    if remaining_secs <= 0 and attempt.status == AttemptStatus.IN_PROGRESS:
        evaluate_attempt(db, attempt.id)
        raise HTTPException(status_code=400, detail="Paper attempt timer has expired.")

    q_docs = list(db.questions.find(
        {"past_year_paper_id": paper.id, "language": req.language},
        sort=[("question_order", ASCENDING)]
    ))
    q_out = [QuestionClientOut.model_validate(q) for q in q_docs]

    user_answers = list(db.answers.find({"attempt_id": attempt.id}))
    answers_dict = {ans["question_group_id"]: ans["selected_option"] for ans in user_answers}

    status_str = attempt.status.value if hasattr(attempt.status, 'value') else str(attempt.status)

    return {
        "attempt_id": attempt.id,
        "past_year_paper_id": paper.id,
        "test_title": paper.title,
        "exam_name": exam_name,
        "duration_minutes": paper.duration_minutes,
        "remaining_seconds": remaining_secs,
        "status": status_str,
        "allowed_languages": allowed_langs,
        "current_language": req.language,
        "questions": q_out,
        "saved_answers": answers_dict
    }

@router.get("/attempts/{attempt_id}")
def get_paper_attempt_status(
    attempt_id: int,
    language: str = "ta",
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    attempt_doc = db.test_attempts.find_one({"id": attempt_id, "user_id": current_user.id})
    if not attempt_doc or not attempt_doc.get("past_year_paper_id"):
        raise HTTPException(status_code=404, detail="Paper attempt not found")

    attempt = to_mongo_doc(attempt_doc)
    paper_doc = db.past_year_papers.find_one({"id": attempt.past_year_paper_id})
    paper = to_mongo_doc(paper_doc)

    exam_doc = db.exams.find_one({"id": paper.exam_id}) if paper.exam_id else None
    exam_name = exam_doc["name"] if exam_doc else ""
    exam_slug = exam_doc["slug"] if exam_doc else ""
    cfg = EXAM_CONFIG.get(exam_slug)
    allowed_langs = cfg["allowed_languages"] if cfg else ["ta"]

    remaining_secs = check_and_get_remaining_seconds(attempt, paper.duration_minutes)
    if remaining_secs <= 0 and attempt.status == AttemptStatus.IN_PROGRESS:
        attempt = evaluate_attempt(db, attempt.id)

    q_docs = list(db.questions.find(
        {"past_year_paper_id": paper.id, "language": language},
        sort=[("question_order", ASCENDING)]
    ))
    q_out = [QuestionClientOut.model_validate(q) for q in q_docs]

    user_answers = list(db.answers.find({"attempt_id": attempt.id}))
    answers_dict = {ans["question_group_id"]: ans["selected_option"] for ans in user_answers}

    status_str = attempt.status.value if hasattr(attempt.status, 'value') else str(attempt.status)

    return {
        "attempt_id": attempt.id,
        "past_year_paper_id": paper.id,
        "test_title": paper.title,
        "exam_name": exam_name,
        "duration_minutes": paper.duration_minutes,
        "remaining_seconds": remaining_secs,
        "status": status_str,
        "allowed_languages": allowed_langs,
        "current_language": language,
        "questions": q_out,
        "saved_answers": answers_dict
    }

@router.post("/attempts/{attempt_id}/answer")
def auto_save_paper_answer(
    attempt_id: int,
    req: SaveAnswerRequest,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    attempt_doc = db.test_attempts.find_one({"id": attempt_id, "user_id": current_user.id})
    if not attempt_doc or not attempt_doc.get("past_year_paper_id"):
        raise HTTPException(status_code=404, detail="Paper attempt not found")

    attempt = to_mongo_doc(attempt_doc)
    if attempt.status != AttemptStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Attempt is already completed or expired")

    paper_doc = db.past_year_papers.find_one({"id": attempt.past_year_paper_id})
    paper = to_mongo_doc(paper_doc)
    if check_and_get_remaining_seconds(attempt, paper.duration_minutes) <= 0:
        evaluate_attempt(db, attempt.id)
        raise HTTPException(status_code=400, detail="Timer expired. Paper attempt submitted automatically.")

    db.answers.update_one(
        {"attempt_id": attempt.id, "question_group_id": req.question_group_id},
        {"$set": {"selected_option": req.selected_option, "answered_at": datetime.utcnow()}},
        upsert=True
    )
    return {"status": "saved", "question_group_id": req.question_group_id, "selected_option": req.selected_option}

@router.post("/attempts/{attempt_id}/submit")
def submit_paper_attempt(
    attempt_id: int,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    attempt_doc = db.test_attempts.find_one({"id": attempt_id, "user_id": current_user.id})
    if not attempt_doc or not attempt_doc.get("past_year_paper_id"):
        raise HTTPException(status_code=404, detail="Paper attempt not found")

    evaluated = evaluate_attempt(db, attempt_id)
    status_str = evaluated.status.value if hasattr(evaluated.status, 'value') else str(evaluated.status)

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
        "status": status_str
    }

@router.get("/attempts/{attempt_id}/result", response_model=ResultOut)
def get_paper_attempt_result(
    attempt_id: int,
    language: str = "ta",
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    attempt_doc = db.test_attempts.find_one({"id": attempt_id, "user_id": current_user.id})
    if not attempt_doc or not attempt_doc.get("past_year_paper_id"):
        raise HTTPException(status_code=404, detail="Paper attempt not found")

    attempt = to_mongo_doc(attempt_doc)
    if attempt.status != AttemptStatus.SUBMITTED:
        attempt = evaluate_attempt(db, attempt.id)

    paper_doc = db.past_year_papers.find_one({"id": attempt.past_year_paper_id})
    paper = to_mongo_doc(paper_doc)

    exam_doc = db.exams.find_one({"id": paper.exam_id}) if paper.exam_id else None
    exam_name = exam_doc["name"] if exam_doc else ""
    exam_slug = exam_doc["slug"] if exam_doc else ""
    cfg = EXAM_CONFIG.get(exam_slug)
    allowed_langs = cfg["allowed_languages"] if cfg else ["ta"]

    q_docs = list(db.questions.find(
        {"past_year_paper_id": paper.id, "language": language},
        sort=[("question_order", ASCENDING)]
    ))
    questions = [to_mongo_doc(q) for q in q_docs]

    user_answers_docs = list(db.answers.find({"attempt_id": attempt.id}))
    answers_map = {ans["question_group_id"]: to_mongo_doc(ans) for ans in user_answers_docs}

    reviews = []
    for q in questions:
        ans = answers_map.get(q.question_group_id)
        stud_ans = ans.selected_option if ans else None
        if not stud_ans:
            st = "Unanswered"
        elif str(stud_ans).upper() == str(q.correct_option).upper():
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
        exam_name=exam_name,
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
