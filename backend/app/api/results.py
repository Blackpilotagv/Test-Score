from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pymongo import DESCENDING, ASCENDING
from app.database.session import get_db
from app.models.models import AttemptStatus, to_mongo_doc
from app.schemas.schemas import ResultOut, AttemptSummaryOut, QuestionReviewOut
from app.api.deps import get_current_user
from app.core.config import EXAM_CONFIG

router = APIRouter(prefix="/results", tags=["Results"])

@router.get("", response_model=List[AttemptSummaryOut])
def get_user_results(
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    attempts_docs = list(db.test_attempts.find(
        {"user_id": current_user.id, "status": AttemptStatus.SUBMITTED},
        sort=[("submitted_at", DESCENDING)]
    ))

    res = []
    for a_doc in attempts_docs:
        a = to_mongo_doc(a_doc)
        test_doc = db.tests.find_one({"id": a.test_id}) if a.test_id else None
        test_title = test_doc["title"] if test_doc else ""
        exam_name = ""
        if test_doc:
            exam_doc = db.exams.find_one({"id": test_doc["exam_id"]})
            exam_name = exam_doc["name"] if exam_doc else ""

        res.append(AttemptSummaryOut(
            attempt_id=a.id,
            test_id=a.test_id,
            test_title=test_title,
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
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    attempt_doc = db.test_attempts.find_one({"id": attempt_id})
    if not attempt_doc:
        raise HTTPException(status_code=404, detail="Result not found")
    attempt = to_mongo_doc(attempt_doc)

    role_str = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
    if attempt.user_id != current_user.id and role_str != "ADMIN":
        raise HTTPException(status_code=403, detail="Unauthorized access to test result")

    if attempt.status != AttemptStatus.SUBMITTED:
        raise HTTPException(status_code=400, detail="Test attempt is not yet submitted.")

    test_doc = db.tests.find_one({"id": attempt.test_id})
    test = to_mongo_doc(test_doc)

    exam_doc = db.exams.find_one({"id": test.exam_id}) if test else None
    exam_name = exam_doc["name"] if exam_doc else ""
    exam_slug = exam_doc["slug"] if exam_doc else ""

    cfg = EXAM_CONFIG.get(exam_slug)
    allowed_langs = cfg["allowed_languages"] if cfg else ["ta"]

    if language not in allowed_langs:
        language = allowed_langs[0]

    if attempt.question_set_id:
        q_docs = list(db.questions.find(
            {"question_set_id": attempt.question_set_id, "language": language},
            sort=[("question_order", ASCENDING)]
        ))
        if not q_docs:
            q_docs = list(db.questions.find(
                {"question_set_id": attempt.question_set_id, "language": "ta"},
                sort=[("question_order", ASCENDING)]
            ))
    else:
        q_docs = list(db.questions.find(
            {"test_id": test.id, "language": language},
            sort=[("question_order", ASCENDING)]
        ))
        if not q_docs:
            q_docs = list(db.questions.find(
                {"test_id": test.id, "language": "ta"},
                sort=[("question_order", ASCENDING)]
            ))

    questions = [to_mongo_doc(q) for q in q_docs]

    user_answers_docs = list(db.answers.find({"attempt_id": attempt.id}))
    answers_map = {ans["question_group_id"]: to_mongo_doc(ans) for ans in user_answers_docs}

    reviews = []
    for q in questions:
        ans = answers_map.get(q.question_group_id)
        student_ans = ans.selected_option if ans else None

        if not student_ans:
            q_status = "Not Answered"
        elif str(student_ans).upper() == str(q.correct_option).upper():
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
