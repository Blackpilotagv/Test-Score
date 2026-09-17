from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo import DESCENDING, ASCENDING
from app.database.session import get_db, get_next_sequence
from app.models.models import PaymentStatus, AttemptStatus, QuestionSetStatus, to_mongo_doc, to_mongo_docs
from app.schemas.schemas import StartAttemptRequest, SaveAnswerRequest, QuestionClientOut
from app.api.deps import get_current_user
from app.services.eval_service import evaluate_attempt, check_and_get_remaining_seconds
from app.core.config import EXAM_CONFIG

router = APIRouter(prefix="/attempts", tags=["Exam Attempts Engine"])

def validate_language_for_test(db, test, requested_lang: str):
    exam_doc = db.exams.find_one({"id": test.exam_id})
    exam_slug = exam_doc["slug"] if exam_doc else ""
    cfg = EXAM_CONFIG.get(exam_slug)
    allowed = cfg["allowed_languages"] if cfg else ["ta"]
    if requested_lang not in allowed:
        exam_name = exam_doc["name"] if exam_doc else "this exam"
        raise HTTPException(
            status_code=400,
            detail=f"Language '{requested_lang}' is not supported for {exam_name}. Allowed: {allowed}"
        )
    return allowed

@router.post("/start")
def start_exam_attempt(
    req: StartAttemptRequest,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    test_doc = db.tests.find_one({"id": req.test_id})
    if not test_doc:
        raise HTTPException(status_code=404, detail="Daily test not found")
    test = to_mongo_doc(test_doc)

    allowed_langs = validate_language_for_test(db, test, req.language)

    # Access control: Must have SUCCESS payment record
    payment = db.payments.find_one({
        "user_id": current_user.id,
        "test_id": test.id,
        "status": PaymentStatus.SUCCESS
    })

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized. You must purchase this test before attending."
        )

    # Check for active attempt
    attempt_doc = db.test_attempts.find_one(
        {"user_id": current_user.id, "test_id": test.id},
        sort=[("id", DESCENDING)]
    )
    attempt = to_mongo_doc(attempt_doc)

    if not attempt or attempt.status == AttemptStatus.SUBMITTED:
        # Check for currently ACTIVE QuestionSet for this test
        active_set_doc = db.question_sets.find_one(
            {"test_id": test.id, "status": QuestionSetStatus.ACTIVE},
            sort=[("id", DESCENDING)]
        )
        active_set = to_mongo_doc(active_set_doc)

        if active_set:
            groups = db.questions.distinct("question_group_id", {"question_set_id": active_set.id})
            unique_groups = len(groups)
        else:
            groups = db.questions.distinct("question_group_id", {"test_id": test.id, "question_set_id": None})
            unique_groups = len(groups)
            if unique_groups == 0:
                next_set_doc = db.question_sets.find_one(
                    {"test_id": test.id, "status": QuestionSetStatus.SCHEDULED},
                    sort=[("schedule_date", ASCENDING)]
                )
                msg = f"Today's daily test is not currently available. Next test starts at 12:00 PM IST on {next_set_doc['schedule_date']}." if next_set_doc else "Today's daily test is not currently available. Next test starts at 12:00 PM IST."
                raise HTTPException(status_code=400, detail=msg)

        attempt_id = get_next_sequence(db, "attempt_id")
        now = datetime.utcnow()
        new_attempt = {
            "id": attempt_id,
            "user_id": current_user.id,
            "test_id": test.id,
            "question_set_id": active_set.id if active_set else None,
            "past_year_paper_id": None,
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

    duration_mins = test.duration_minutes if test else 30
    remaining_secs = check_and_get_remaining_seconds(attempt, duration_mins)
    if remaining_secs <= 0 and attempt.status == AttemptStatus.IN_PROGRESS:
        evaluate_attempt(db, attempt.id)
        raise HTTPException(status_code=400, detail="Exam timer has already expired for this attempt.")

    if attempt.question_set_id:
        q_docs = list(db.questions.find(
            {"question_set_id": attempt.question_set_id, "language": req.language},
            sort=[("question_order", ASCENDING)]
        ))
    else:
        q_docs = list(db.questions.find(
            {"test_id": test.id, "language": req.language},
            sort=[("question_order", ASCENDING)]
        ))

    q_out = [QuestionClientOut.model_validate(q) for q in q_docs]

    user_answers = list(db.answers.find({"attempt_id": attempt.id}))
    answers_dict = {ans["question_group_id"]: ans["selected_option"] for ans in user_answers}

    exam_doc = db.exams.find_one({"id": test.exam_id})
    exam_name = exam_doc["name"] if exam_doc else ""

    status_str = attempt.status.value if isinstance(attempt.status, AttemptStatus) else str(attempt.status)

    return {
        "attempt_id": attempt.id,
        "test_id": test.id,
        "test_title": test.title,
        "exam_name": exam_name,
        "duration_minutes": test.duration_minutes,
        "remaining_seconds": remaining_secs,
        "status": status_str,
        "allowed_languages": allowed_langs,
        "current_language": req.language,
        "questions": q_out,
        "saved_answers": answers_dict
    }

@router.get("/{attempt_id}")
def get_attempt_status(
    attempt_id: int,
    language: str = "ta",
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    attempt_doc = db.test_attempts.find_one({"id": attempt_id, "user_id": current_user.id})
    if not attempt_doc:
        raise HTTPException(status_code=404, detail="Attempt not found")
    attempt = to_mongo_doc(attempt_doc)

    test_doc = db.tests.find_one({"id": attempt.test_id})
    test = to_mongo_doc(test_doc)

    allowed_langs = validate_language_for_test(db, test, language)
    duration_mins = test.duration_minutes if test else 30
    remaining_secs = check_and_get_remaining_seconds(attempt, duration_mins)

    if remaining_secs <= 0 and attempt.status == AttemptStatus.IN_PROGRESS:
        attempt = evaluate_attempt(db, attempt.id)

    if attempt.question_set_id:
        q_docs = list(db.questions.find(
            {"question_set_id": attempt.question_set_id, "language": language},
            sort=[("question_order", ASCENDING)]
        ))
    else:
        q_docs = list(db.questions.find(
            {"test_id": test.id, "language": language},
            sort=[("question_order", ASCENDING)]
        ))

    q_out = [QuestionClientOut.model_validate(q) for q in q_docs]

    user_answers = list(db.answers.find({"attempt_id": attempt.id}))
    answers_dict = {ans["question_group_id"]: ans["selected_option"] for ans in user_answers}

    exam_doc = db.exams.find_one({"id": test.exam_id})
    exam_name = exam_doc["name"] if exam_doc else ""

    status_str = attempt.status.value if isinstance(attempt.status, AttemptStatus) else str(attempt.status)

    return {
        "attempt_id": attempt.id,
        "test_id": test.id,
        "test_title": test.title,
        "exam_name": exam_name,
        "duration_minutes": test.duration_minutes,
        "remaining_seconds": remaining_secs,
        "status": status_str,
        "allowed_languages": allowed_langs,
        "current_language": language,
        "questions": q_out,
        "saved_answers": answers_dict
    }

@router.post("/{attempt_id}/answer")
def auto_save_answer(
    attempt_id: int,
    req: SaveAnswerRequest,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    attempt_doc = db.test_attempts.find_one({"id": attempt_id, "user_id": current_user.id})
    if not attempt_doc:
        raise HTTPException(status_code=404, detail="Attempt not found")
    attempt = to_mongo_doc(attempt_doc)

    if attempt.status != AttemptStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Cannot edit answers for completed or expired attempt")

    test_doc = db.tests.find_one({"id": attempt.test_id})
    duration_mins = test_doc["duration_minutes"] if test_doc else 30
    if check_and_get_remaining_seconds(attempt, duration_mins) <= 0:
        evaluate_attempt(db, attempt.id)
        raise HTTPException(status_code=400, detail="Timer expired. Test submitted automatically.")

    db.answers.update_one(
        {"attempt_id": attempt.id, "question_group_id": req.question_group_id},
        {"$set": {
            "selected_option": req.selected_option,
            "answered_at": datetime.utcnow()
        }},
        upsert=True
    )
    return {"status": "saved", "question_group_id": req.question_group_id, "selected_option": req.selected_option}

@router.post("/{attempt_id}/submit")
def submit_exam_attempt(
    attempt_id: int,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    attempt_doc = db.test_attempts.find_one({"id": attempt_id, "user_id": current_user.id})
    if not attempt_doc:
        raise HTTPException(status_code=404, detail="Attempt not found")

    evaluated_attempt = evaluate_attempt(db, attempt_id)
    status_str = evaluated_attempt.status.value if isinstance(evaluated_attempt.status, AttemptStatus) else str(evaluated_attempt.status)

    return {
        "attempt_id": evaluated_attempt.id,
        "score": evaluated_attempt.score,
        "percentage": evaluated_attempt.percentage,
        "correct_answers": evaluated_attempt.correct_answers,
        "wrong_answers": evaluated_attempt.wrong_answers,
        "unanswered": evaluated_attempt.unanswered,
        "total_questions": evaluated_attempt.total_questions,
        "time_taken": evaluated_attempt.time_taken,
        "status": status_str
    }
