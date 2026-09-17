from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pymongo import DESCENDING, ASCENDING
from app.database.session import get_db
from app.models.models import TestStatus, PaymentStatus, QuestionSetStatus, to_mongo_doc
from app.schemas.schemas import TestOut
from app.api.deps import oauth2_scheme
from app.core.config import EXAM_CONFIG, settings
from jose import jwt

router = APIRouter(prefix="/tests", tags=["Tests"])

def check_user_access(db, user_id: int, test_id: int) -> bool:
    payment = db.payments.find_one({
        "user_id": user_id,
        "test_id": test_id,
        "status": PaymentStatus.SUCCESS
    })
    return payment is not None

def get_allowed_languages(exam_slug: str) -> List[str]:
    cfg = EXAM_CONFIG.get(exam_slug)
    if cfg:
        return cfg["allowed_languages"]
    return ["ta"]

def get_question_set_info(db, test_id: int):
    """Helper to check active QuestionSet and next scheduled publish date."""
    active_set = db.question_sets.find_one(
        {"test_id": test_id, "status": QuestionSetStatus.ACTIVE},
        sort=[("id", DESCENDING)]
    )

    if active_set:
        return True, active_set["id"], f"Active set available (Date: {active_set['schedule_date']})"

    next_sched = db.question_sets.find_one(
        {"test_id": test_id, "status": QuestionSetStatus.SCHEDULED},
        sort=[("schedule_date", ASCENDING)]
    )

    if next_sched:
        return False, None, f"Next test scheduled for {next_sched['schedule_date']} at 12:00 PM IST."

    return False, None, "Today's daily test is not currently available. Next test starts at 12:00 PM IST."

@router.get("", response_model=List[TestOut])
def get_published_tests(
    exam_id: Optional[int] = None,
    db = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
):
    user_id = None
    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = int(payload.get("sub"))
        except Exception:
            pass

    query_filter = {"status": TestStatus.PUBLISHED}
    if exam_id:
        query_filter["exam_id"] = exam_id

    tests_list = list(db.tests.find(query_filter, sort=[("id", DESCENDING)]))
    result = []

    for t_doc in tests_list:
        t = to_mongo_doc(t_doc)
        has_access = False
        if user_id:
            has_access = check_user_access(db, user_id, t.id)
        
        exam_doc = db.exams.find_one({"id": t.exam_id})
        exam_name = exam_doc["name"] if exam_doc else ""
        exam_slug = exam_doc["slug"] if exam_doc else ""
        allowed_langs = get_allowed_languages(exam_slug)
        has_active, active_id, next_info = get_question_set_info(db, t.id)

        test_dto = TestOut(
            id=t.id,
            exam_id=t.exam_id,
            exam_name=exam_name,
            exam_slug=exam_slug,
            allowed_languages=allowed_langs,
            title=t.title,
            description=t.description,
            test_date=t.test_date,
            duration_minutes=t.duration_minutes,
            question_count=t.question_count,
            price=t.price,
            status=t.status,
            created_at=t.created_at,
            has_access=has_access,
            has_active_set=has_active,
            active_question_set_id=active_id,
            next_publish_info=next_info
        )
        result.append(test_dto)

    return result

@router.get("/{test_id}", response_model=TestOut)
def get_test_details(
    test_id: int,
    db = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
):
    user_id = None
    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = int(payload.get("sub"))
        except Exception:
            pass

    t_doc = db.tests.find_one({"id": test_id})
    if not t_doc:
        raise HTTPException(status_code=404, detail="Daily test not found")

    test = to_mongo_doc(t_doc)
    has_access = False
    if user_id:
        has_access = check_user_access(db, user_id, test.id)

    exam_doc = db.exams.find_one({"id": test.exam_id})
    exam_name = exam_doc["name"] if exam_doc else ""
    exam_slug = exam_doc["slug"] if exam_doc else ""
    allowed_langs = get_allowed_languages(exam_slug)
    has_active, active_id, next_info = get_question_set_info(db, test.id)

    return TestOut(
        id=test.id,
        exam_id=test.exam_id,
        exam_name=exam_name,
        exam_slug=exam_slug,
        allowed_languages=allowed_langs,
        title=test.title,
        description=test.description,
        test_date=test.test_date,
        duration_minutes=test.duration_minutes,
        question_count=test.question_count,
        price=test.price,
        status=test.status,
        created_at=test.created_at,
        has_access=has_access,
        has_active_set=has_active,
        active_question_set_id=active_id,
        next_publish_info=next_info
    )
