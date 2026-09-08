from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.session import get_db
from app.models.models import User, TestAttempt, AttemptStatus, Question, Answer
from app.schemas.schemas import ResultOut, AttemptSummaryOut, QuestionReviewOut
from app.api.deps import get_current_user
from app.core.config import EXAM_CONFIG

router = APIRouter(prefix="/results", tags=["Results"])

@router.get("", response_model=List[AttemptSummaryOut])
def get_user_results(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    attempts = db.query(TestAttempt).filter(
        TestAttempt.user_id == current_user.id,
        TestAttempt.status == AttemptStatus.SUBMITTED
    ).order_by(TestAttempt.submitted_at.desc()).all()

    res = []
    for a in attempts:
        exam_name = a.test.exam.name if a.test and a.test.exam else ""
        res.append(AttemptSummaryOut(
            attempt_id=a.id,
            test_id=a.test_id,
            test_title=a.test.title if a.test else "",
            exam_name=exam_name,
            submitted_at=a.submitted_at,
            score=a.score,
            total_questions=a.total_questions,
            percentage=a.percentage,
            time_taken=a.time_taken
        ))
    return res

@router.get("/{attempt_id}", response_model=ResultOut)
def get_detailed_result(
    attempt_id: int,
    language: str = "ta",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    attempt = db.query(TestAttempt).filter(TestAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Result not found")

    if attempt.user_id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Unauthorized access to test result")

    if attempt.status != AttemptStatus.SUBMITTED:
        raise HTTPException(status_code=400, detail="Test attempt is not yet submitted.")

    test = attempt.test
    exam_name = test.exam.name if test and test.exam else ""
    exam_slug = test.exam.slug if test and test.exam else ""
    cfg = EXAM_CONFIG.get(exam_slug)
    allowed_langs = cfg["allowed_languages"] if cfg else ["ta"]

    if language not in allowed_langs:
        language = allowed_langs[0]

    # Fetch questions for requested language
    questions = db.query(Question).filter(
        Question.test_id == test.id,
        Question.language == language
    ).order_by(Question.question_order.asc()).all()

    # Fallback to Tamil if requested language questions aren't present
    if not questions:
        questions = db.query(Question).filter(
            Question.test_id == test.id,
            Question.language == "ta"
        ).order_by(Question.question_order.asc()).all()

    # Fetch student answers
    user_answers = db.query(Answer).filter(Answer.attempt_id == attempt.id).all()
    answers_map = {ans.question_group_id: ans for ans in user_answers}

    reviews = []
    for q in questions:
        ans = answers_map.get(q.question_group_id)
        student_ans = ans.selected_option if ans else None
        
        if not student_ans:
            q_status = "Not Answered"
        elif student_ans.upper() == q.correct_option.upper():
            q_status = "Correct"
        else:
            q_status = "Incorrect"

        reviews.append(QuestionReviewOut(
            question_group_id=q.question_group_id,
            question_order=q.question_order,
            language=q.language,
            question_text=q.question_text,
            option_a=q.option_a,
            option_b=q.option_b,
            option_c=q.option_c,
            option_d=q.option_d,
            student_answer=student_ans,
            correct_answer=q.correct_option,
            status=q_status,
            explanation=q.explanation
        ))

    return ResultOut(
        attempt_id=attempt.id,
        test_id=test.id,
        test_title=test.title,
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
