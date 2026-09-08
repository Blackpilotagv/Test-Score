from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.database.session import get_db
from app.models.models import User, Test, Payment, PaymentStatus, TestAttempt, AttemptStatus, Question, Answer
from app.schemas.schemas import StartAttemptRequest, SaveAnswerRequest, QuestionClientOut
from app.api.deps import get_current_user
from app.services.eval_service import evaluate_attempt, check_and_get_remaining_seconds
from app.core.config import EXAM_CONFIG

router = APIRouter(prefix="/attempts", tags=["Exam Attempts Engine"])

from app.models.models import User, Test, Payment, PaymentStatus, TestAttempt, AttemptStatus, Question, Answer, QuestionSet, QuestionSetStatus

def validate_language_for_test(test: Test, requested_lang: str):
    exam_slug = test.exam.slug if test.exam else ""
    cfg = EXAM_CONFIG.get(exam_slug)
    allowed = cfg["allowed_languages"] if cfg else ["ta"]
    if requested_lang not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Language '{requested_lang}' is not supported for {test.exam.name}. Allowed: {allowed}"
        )
    return allowed

@router.post("/start")
def start_exam_attempt(
    req: StartAttemptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    test = db.query(Test).filter(Test.id == req.test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Daily test not found")

    allowed_langs = validate_language_for_test(test, req.language)

    # Access control: Must have SUCCESS payment record
    payment = db.query(Payment).filter(
        Payment.user_id == current_user.id,
        Payment.test_id == test.id,
        Payment.status == PaymentStatus.SUCCESS
    ).first()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized. You must purchase this test before attending."
        )

    # Check for active attempt
    attempt = db.query(TestAttempt).filter(
        TestAttempt.user_id == current_user.id,
        TestAttempt.test_id == test.id
    ).order_by(TestAttempt.id.desc()).first()

    if not attempt or attempt.status == AttemptStatus.SUBMITTED:
        # Check for currently ACTIVE QuestionSet for this test
        active_set = db.query(QuestionSet).filter(
            QuestionSet.test_id == test.id,
            QuestionSet.status == QuestionSetStatus.ACTIVE
        ).order_by(QuestionSet.id.desc()).first()

        # If no active set exists, fallback to questions directly under test_id (legacy) or reject
        q_count_query = db.query(Question.question_group_id)
        if active_set:
            q_count_query = q_count_query.filter(Question.question_set_id == active_set.id)
        else:
            # Check if direct test questions exist without sets
            legacy_count = db.query(Question.question_group_id).filter(Question.test_id == test.id, Question.question_set_id == None).distinct().count()
            if legacy_count == 0:
                # Check next scheduled publish date
                next_set = db.query(QuestionSet).filter(
                    QuestionSet.test_id == test.id,
                    QuestionSet.status == QuestionSetStatus.SCHEDULED
                ).order_by(QuestionSet.schedule_date.asc()).first()
                msg = f"Today's daily test is not currently available. Next test starts at 12:00 PM IST on {next_set.schedule_date}." if next_set else "Today's daily test is not currently available. Next test starts at 12:00 PM IST."
                raise HTTPException(status_code=400, detail=msg)
            q_count_query = q_count_query.filter(Question.test_id == test.id, Question.question_set_id == None)

        unique_groups = q_count_query.distinct().count()

        attempt = TestAttempt(
            user_id=current_user.id,
            test_id=test.id,
            question_set_id=active_set.id if active_set else None,
            started_at=datetime.utcnow(),
            status=AttemptStatus.IN_PROGRESS,
            total_questions=unique_groups
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)

    duration_mins = test.duration_minutes if test else 30
    remaining_secs = check_and_get_remaining_seconds(attempt, duration_mins)
    if remaining_secs <= 0 and attempt.status == AttemptStatus.IN_PROGRESS:
        evaluate_attempt(db, attempt.id)
        raise HTTPException(status_code=400, detail="Exam timer has already expired for this attempt.")

    # Return questions specifically bound to attempt's question_set_id
    if attempt.question_set_id:
        questions = db.query(Question).filter(
            Question.question_set_id == attempt.question_set_id,
            Question.language == req.language
        ).order_by(Question.question_order.asc()).all()
    else:
        questions = db.query(Question).filter(
            Question.test_id == test.id,
            Question.language == req.language
        ).order_by(Question.question_order.asc()).all()

    q_out = [QuestionClientOut.model_validate(q) for q in questions]

    # Return existing answers map (question_group_id -> selected_option)
    user_answers = db.query(Answer).filter(Answer.attempt_id == attempt.id).all()
    answers_dict = {ans.question_group_id: ans.selected_option for ans in user_answers}

    return {
        "attempt_id": attempt.id,
        "test_id": test.id,
        "test_title": test.title,
        "exam_name": test.exam.name if test.exam else "",
        "duration_minutes": test.duration_minutes,
        "remaining_seconds": remaining_secs,
        "status": attempt.status.value,
        "allowed_languages": allowed_langs,
        "current_language": req.language,
        "questions": q_out,
        "saved_answers": answers_dict
    }

@router.get("/{attempt_id}")
def get_attempt_status(
    attempt_id: int,
    language: str = "ta",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    attempt = db.query(TestAttempt).filter(
        TestAttempt.id == attempt_id,
        TestAttempt.user_id == current_user.id
    ).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    test = attempt.test
    allowed_langs = validate_language_for_test(test, language)
    duration_mins = test.duration_minutes if test else 30
    remaining_secs = check_and_get_remaining_seconds(attempt, duration_mins)

    if remaining_secs <= 0 and attempt.status == AttemptStatus.IN_PROGRESS:
        attempt = evaluate_attempt(db, attempt.id)

    if attempt.question_set_id:
        questions = db.query(Question).filter(
            Question.question_set_id == attempt.question_set_id,
            Question.language == language
        ).order_by(Question.question_order.asc()).all()
    else:
        questions = db.query(Question).filter(
            Question.test_id == test.id,
            Question.language == language
        ).order_by(Question.question_order.asc()).all()

    q_out = [QuestionClientOut.model_validate(q) for q in questions]

    user_answers = db.query(Answer).filter(Answer.attempt_id == attempt.id).all()
    answers_dict = {ans.question_group_id: ans.selected_option for ans in user_answers}


    return {
        "attempt_id": attempt.id,
        "test_id": test.id,
        "test_title": test.title,
        "exam_name": test.exam.name if test.exam else "",
        "duration_minutes": test.duration_minutes,
        "remaining_seconds": remaining_secs,
        "status": attempt.status.value,
        "allowed_languages": allowed_langs,
        "current_language": language,
        "questions": q_out,
        "saved_answers": answers_dict
    }

@router.post("/{attempt_id}/answer")
def auto_save_answer(
    attempt_id: int,
    req: SaveAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    attempt = db.query(TestAttempt).filter(
        TestAttempt.id == attempt_id,
        TestAttempt.user_id == current_user.id
    ).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    if attempt.status != AttemptStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Cannot edit answers for completed or expired attempt")

    duration_mins = test.duration_minutes if test else 30
    if check_and_get_remaining_seconds(attempt, duration_mins) <= 0:
        evaluate_attempt(db, attempt.id)
        raise HTTPException(status_code=400, detail="Timer expired. Test submitted automatically.")

    # Find existing answer record by question_group_id
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

@router.post("/{attempt_id}/submit")
def submit_exam_attempt(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    attempt = db.query(TestAttempt).filter(
        TestAttempt.id == attempt_id,
        TestAttempt.user_id == current_user.id
    ).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    evaluated_attempt = evaluate_attempt(db, attempt.id)
    return {
        "attempt_id": evaluated_attempt.id,
        "score": evaluated_attempt.score,
        "percentage": evaluated_attempt.percentage,
        "correct_answers": evaluated_attempt.correct_answers,
        "wrong_answers": evaluated_attempt.wrong_answers,
        "unanswered": evaluated_attempt.unanswered,
        "total_questions": evaluated_attempt.total_questions,
        "time_taken": evaluated_attempt.time_taken,
        "status": evaluated_attempt.status.value
    }
