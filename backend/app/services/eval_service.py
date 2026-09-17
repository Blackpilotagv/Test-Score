from datetime import datetime
from app.models.models import AttemptStatus, to_mongo_doc

def evaluate_attempt(db, attempt_id: int):
    """
    Evaluates a test attempt server-side in MongoDB.
    Counts logical questions (unique question_group_id) ONCE.
    Calculates correct, wrong, unanswered, score, percentage, and time taken.
    Supports custom scoring formulas for PastYearPaper (marks_per_question & negative_mark).
    """
    attempt_doc = db.test_attempts.find_one({"id": attempt_id})
    if not attempt_doc:
        raise ValueError("Attempt not found")

    attempt = to_mongo_doc(attempt_doc)

    if attempt.status == AttemptStatus.SUBMITTED:
        return attempt

    marks_per_question = 1.0
    negative_mark = 0.0

    if attempt.past_year_paper_id:
        paper_doc = db.past_year_papers.find_one({"id": attempt.past_year_paper_id})
        if paper_doc:
            marks_per_question = float(paper_doc.get("marks_per_question", 1.5))
            negative_mark = float(paper_doc.get("negative_mark", 0.0))
        q_docs = list(db.questions.find({"past_year_paper_id": attempt.past_year_paper_id}))
    elif attempt.question_set_id:
        q_docs = list(db.questions.find({"question_set_id": attempt.question_set_id}))
    else:
        q_docs = list(db.questions.find({"test_id": attempt.test_id}))

    group_map = {}
    for q in q_docs:
        q_obj = to_mongo_doc(q)
        if q_obj.question_group_id not in group_map or q_obj.language == 'ta':
            group_map[q_obj.question_group_id] = q_obj

    total_questions = len(group_map)

    user_answers_docs = list(db.answers.find({"attempt_id": attempt.id}))
    answers_map = {ans["question_group_id"]: to_mongo_doc(ans) for ans in user_answers_docs}

    correct_count = 0
    wrong_count = 0
    unanswered_count = 0

    for q_group_id, q_master in group_map.items():
        ans = answers_map.get(q_group_id)
        if not ans or not ans.get("selected_option"):
            unanswered_count += 1
            if ans:
                db.answers.update_one({"attempt_id": attempt.id, "question_group_id": q_group_id}, {"$set": {"is_correct": False}})
        else:
            sel_opt = str(ans.selected_option).upper()
            corr_opt = str(q_master.correct_option).upper()
            if sel_opt == corr_opt:
                correct_count += 1
                db.answers.update_one({"attempt_id": attempt.id, "question_group_id": q_group_id}, {"$set": {"is_correct": True}})
            else:
                wrong_count += 1
                db.answers.update_one({"attempt_id": attempt.id, "question_group_id": q_group_id}, {"$set": {"is_correct": False}})

    score = (correct_count * marks_per_question) - (wrong_count * negative_mark)
    score = max(0.0, score)

    max_possible_score = total_questions * marks_per_question
    percentage = (score / max_possible_score * 100.0) if max_possible_score > 0 else 0.0

    now = datetime.utcnow()
    started_at = attempt.started_at
    if isinstance(started_at, str):
        try:
            started_at = datetime.fromisoformat(started_at)
        except Exception:
            started_at = now

    duration_seconds = int((now - started_at).total_seconds())
    minutes = max(0, duration_seconds // 60)
    seconds = max(0, duration_seconds % 60)
    time_taken_str = f"{minutes:02d}:{seconds:02d}"

    updated_fields = {
        "submitted_at": now,
        "status": AttemptStatus.SUBMITTED,
        "score": round(score, 2),
        "correct_answers": correct_count,
        "wrong_answers": wrong_count,
        "unanswered": unanswered_count,
        "total_questions": total_questions,
        "percentage": round(percentage, 2),
        "time_taken": time_taken_str
    }

    db.test_attempts.update_one({"id": attempt.id}, {"$set": updated_fields})
    updated_doc = db.test_attempts.find_one({"id": attempt.id})
    return to_mongo_doc(updated_doc)

def check_and_get_remaining_seconds(attempt, duration_minutes: int) -> int:
    """Calculates remaining seconds based on server-side started_at time."""
    now = datetime.utcnow()
    started_at = attempt.started_at
    if isinstance(started_at, str):
        try:
            started_at = datetime.fromisoformat(started_at)
        except Exception:
            started_at = now

    elapsed = int((now - started_at).total_seconds())
    total_allowed = duration_minutes * 60
    remaining = total_allowed - elapsed
    return max(0, remaining)
