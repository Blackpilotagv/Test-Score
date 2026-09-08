from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.models import TestAttempt, Answer, Question, AttemptStatus, Test, PastYearPaper

def evaluate_attempt(db: Session, attempt_id: int) -> TestAttempt:
    """
    Evaluates a test attempt server-side.
    Counts logical questions (unique question_group_id) ONCE.
    Calculates correct, wrong, unanswered, score, percentage, and time taken.
    Supports custom scoring formulas for PastYearPaper (marks_per_question & negative_mark).
    """
    attempt = db.query(TestAttempt).filter(TestAttempt.id == attempt_id).first()
    if not attempt:
        raise ValueError("Attempt not found")

    if attempt.status == AttemptStatus.SUBMITTED:
        return attempt

    marks_per_question = 1.0
    negative_mark = 0.0

    # Fetch all distinct logical question groups
    if attempt.past_year_paper_id:
        paper = db.query(PastYearPaper).filter(PastYearPaper.id == attempt.past_year_paper_id).first()
        if paper:
            marks_per_question = paper.marks_per_question
            negative_mark = paper.negative_mark
        questions = db.query(Question).filter(Question.past_year_paper_id == attempt.past_year_paper_id).all()
    elif attempt.question_set_id:
        questions = db.query(Question).filter(Question.question_set_id == attempt.question_set_id).all()
    else:
        questions = db.query(Question).filter(Question.test_id == attempt.test_id).all()

    # Map question_group_id -> Question (preferred Tamil or first available)
    group_map = {}
    for q in questions:
        if q.question_group_id not in group_map or q.language == 'ta':
            group_map[q.question_group_id] = q

    total_questions = len(group_map)

    # Fetch student's saved answers
    user_answers = db.query(Answer).filter(Answer.attempt_id == attempt.id).all()
    answers_map = {ans.question_group_id: ans for ans in user_answers}

    correct_count = 0
    wrong_count = 0
    unanswered_count = 0

    for q_group_id, q_master in group_map.items():
        ans = answers_map.get(q_group_id)
        if not ans or not ans.selected_option:
            unanswered_count += 1
            if ans:
                ans.is_correct = False
        else:
            if ans.selected_option.upper() == q_master.correct_option.upper():
                correct_count += 1
                ans.is_correct = True
            else:
                wrong_count += 1
                ans.is_correct = False

    score = (correct_count * marks_per_question) - (wrong_count * negative_mark)
    score = max(0.0, score) # Ensure non-negative total score

    max_possible_score = total_questions * marks_per_question
    percentage = (score / max_possible_score * 100.0) if max_possible_score > 0 else 0.0

    now = datetime.utcnow()
    duration_seconds = int((now - attempt.started_at).total_seconds())
    minutes = duration_seconds // 60
    seconds = duration_seconds % 60
    time_taken_str = f"{minutes:02d}:{seconds:02d}"

    attempt.submitted_at = now
    attempt.status = AttemptStatus.SUBMITTED
    attempt.score = round(score, 2)
    attempt.correct_answers = correct_count
    attempt.wrong_answers = wrong_count
    attempt.unanswered = unanswered_count
    attempt.total_questions = total_questions
    attempt.percentage = round(percentage, 2)
    attempt.time_taken = time_taken_str

    db.commit()
    db.refresh(attempt)
    return attempt


def check_and_get_remaining_seconds(attempt: TestAttempt, duration_minutes: int) -> int:
    """Calculates remaining seconds based on server-side started_at time."""
    now = datetime.utcnow()
    elapsed = int((now - attempt.started_at).total_seconds())
    total_allowed = duration_minutes * 60
    remaining = total_allowed - elapsed
    return max(0, remaining)
