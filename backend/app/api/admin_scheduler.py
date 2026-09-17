from datetime import datetime, date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo import DESCENDING, ASCENDING

from app.database.session import get_db, get_next_sequence
from app.models.models import QuestionSetStatus, to_mongo_doc
from app.schemas.schemas import QuestionSetCreate, QuestionSetUpdate, QuestionSetOut, SchedulerCalendarDay, AuditLogOut
from app.api.deps import get_admin_user
from app.services.scheduler_service import (
    get_current_ist_date,
    get_current_ist_date_str,
    get_ist_12pm_utc,
    validate_schedule_date,
    create_audit_log,
    activate_daily_sets_transaction
)

router = APIRouter(prefix="/admin/question-sets", tags=["Admin Question Scheduler"])

def format_question_set_out(db, qs) -> QuestionSetOut:
    exam_doc = db.exams.find_one({"id": qs.exam_id}) if qs.exam_id else None
    exam_name = exam_doc["name"] if exam_doc else ""
    exam_slug = exam_doc["slug"] if exam_doc else ""

    test_doc = db.tests.find_one({"id": qs.test_id}) if qs.test_id else None
    test_title = test_doc["title"] if test_doc else ""

    q_count = qs.question_count
    if q_count == 0:
        qs_groups = db.questions.distinct("question_group_id", {"question_set_id": qs.id})
        q_count = len(qs_groups)

    status_str = qs.status.value if hasattr(qs.status, "value") else str(qs.status)

    return QuestionSetOut(
        id=qs.id,
        exam_id=qs.exam_id,
        test_id=qs.test_id,
        exam_name=exam_name,
        exam_slug=exam_slug,
        test_title=test_title,
        title=qs.title,
        schedule_date=qs.schedule_date,
        publish_at=qs.publish_at,
        published_at=qs.published_at,
        expire_at=qs.expire_at,
        expired_at=qs.expired_at,
        status=status_str,
        question_count=q_count,
        created_by=qs.created_by,
        created_at=qs.created_at,
        updated_at=qs.updated_at
    )

@router.get("", response_model=List[QuestionSetOut])
def list_question_sets(
    exam_id: Optional[int] = None,
    test_id: Optional[int] = None,
    status_str: Optional[str] = None,
    schedule_date: Optional[str] = None,
    db = Depends(get_db),
    admin = Depends(get_admin_user)
):
    query_filter = {}
    if exam_id:
        query_filter["exam_id"] = exam_id
    if test_id:
        query_filter["test_id"] = test_id
    if status_str:
        query_filter["status"] = status_str.upper()
    if schedule_date:
        query_filter["schedule_date"] = schedule_date

    qs_docs = list(db.question_sets.find(
        query_filter,
        sort=[("schedule_date", DESCENDING), ("id", DESCENDING)]
    ))
    return [format_question_set_out(db, to_mongo_doc(s)) for s in qs_docs]

@router.get("/calendar", response_model=List[SchedulerCalendarDay])
def get_7day_rolling_calendar(
    start_date: Optional[str] = None,
    db = Depends(get_db),
    admin = Depends(get_admin_user)
):
    current_ist = get_current_ist_date()

    if start_date:
        try:
            base_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            base_date = current_ist
    else:
        base_date = current_ist

    calendar_days = []
    max_allowed = current_ist + timedelta(days=7)

    for i in range(7):
        day_date = base_date + timedelta(days=i)
        day_str = day_date.strftime("%Y-%m-%d")
        day_name = day_date.strftime("%A")
        is_today = (day_date == current_ist)
        is_allowed = (day_date >= current_ist and day_date <= max_allowed)

        sets_docs = list(db.question_sets.find({"schedule_date": day_str}))
        formatted_sets = [format_question_set_out(db, to_mongo_doc(s)) for s in sets_docs]

        calendar_days.append(SchedulerCalendarDay(
            date_str=day_str,
            day_name=day_name,
            is_today=is_today,
            is_allowed=is_allowed,
            sets=formatted_sets
        ))

    return calendar_days

@router.post("", response_model=QuestionSetOut)
def create_question_set(
    qs_in: QuestionSetCreate,
    db = Depends(get_db),
    admin = Depends(get_admin_user)
):
    exam_doc = db.exams.find_one({"id": qs_in.exam_id})
    if not exam_doc:
        raise HTTPException(status_code=404, detail="Exam category not found")

    test_doc = db.tests.find_one({"id": qs_in.test_id})
    if not test_doc:
        raise HTTPException(status_code=404, detail="Daily test not found")

    target_date = validate_schedule_date(qs_in.schedule_date)

    existing = db.question_sets.find_one({
        "exam_id": qs_in.exam_id,
        "test_id": qs_in.test_id,
        "schedule_date": qs_in.schedule_date,
        "status": {"$in": [QuestionSetStatus.SCHEDULED, QuestionSetStatus.ACTIVE]}
    })

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"A question set '{existing['title']}' is already {existing['status']} for this test on {qs_in.schedule_date}."
        )

    publish_utc = get_ist_12pm_utc(target_date)
    expire_utc = get_ist_12pm_utc(target_date + timedelta(days=1))
    set_id = get_next_sequence(db, "question_set_id")
    now = datetime.utcnow()

    new_set = {
        "id": set_id,
        "exam_id": qs_in.exam_id,
        "test_id": qs_in.test_id,
        "title": qs_in.title,
        "schedule_date": qs_in.schedule_date,
        "publish_at": publish_utc,
        "published_at": None,
        "expire_at": expire_utc,
        "expired_at": None,
        "status": qs_in.status.upper() if qs_in.status else QuestionSetStatus.DRAFT,
        "question_count": 0,
        "created_by": admin.id,
        "created_at": now,
        "updated_at": now
    }
    db.question_sets.insert_one(new_set)

    create_audit_log(
        db,
        action="QUESTION_SET_CREATED",
        user_id=admin.id,
        question_set_id=set_id,
        details=f"Created question set '{qs_in.title}' for date {qs_in.schedule_date}."
    )

    return format_question_set_out(db, to_mongo_doc(new_set))

@router.get("/{set_id}", response_model=QuestionSetOut)
def get_question_set_detail(
    set_id: int,
    db = Depends(get_db),
    admin = Depends(get_admin_user)
):
    qs_doc = db.question_sets.find_one({"id": set_id})
    if not qs_doc:
        raise HTTPException(status_code=404, detail="Question set not found")
    return format_question_set_out(db, to_mongo_doc(qs_doc))

@router.put("/{set_id}", response_model=QuestionSetOut)
def update_question_set(
    set_id: int,
    qs_in: QuestionSetUpdate,
    db = Depends(get_db),
    admin = Depends(get_admin_user)
):
    qs_doc = db.question_sets.find_one({"id": set_id})
    if not qs_doc:
        raise HTTPException(status_code=404, detail="Question set not found")
    qs = to_mongo_doc(qs_doc)

    if qs.status in [QuestionSetStatus.ACTIVE, QuestionSetStatus.EXPIRED]:
        raise HTTPException(status_code=400, detail=f"Cannot edit a question set in {qs.status} status.")

    update_fields = {"updated_at": datetime.utcnow()}

    if qs_in.schedule_date and qs_in.schedule_date != qs.schedule_date:
        target_date = validate_schedule_date(qs_in.schedule_date)
        existing = db.question_sets.find_one({
            "exam_id": qs.exam_id,
            "test_id": qs.test_id,
            "schedule_date": qs_in.schedule_date,
            "status": {"$in": [QuestionSetStatus.SCHEDULED, QuestionSetStatus.ACTIVE]},
            "id": {"$ne": set_id}
        })
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"A question set is already scheduled for this test on {qs_in.schedule_date}."
            )

        update_fields["schedule_date"] = qs_in.schedule_date
        update_fields["publish_at"] = get_ist_12pm_utc(target_date)
        update_fields["expire_at"] = get_ist_12pm_utc(target_date + timedelta(days=1))

    if qs_in.title:
        update_fields["title"] = qs_in.title

    if qs_in.status:
        update_fields["status"] = qs_in.status.upper()

    db.question_sets.update_one({"id": set_id}, {"$set": update_fields})
    updated_doc = db.question_sets.find_one({"id": set_id})
    updated_qs = to_mongo_doc(updated_doc)

    create_audit_log(
        db,
        action="QUESTION_SET_UPDATED",
        user_id=admin.id,
        question_set_id=set_id,
        details=f"Updated question set #{set_id} title='{updated_qs.title}', date={updated_qs.schedule_date}."
    )

    return format_question_set_out(db, updated_qs)

@router.post("/{set_id}/schedule", response_model=QuestionSetOut)
def schedule_question_set(
    set_id: int,
    schedule_date: Optional[str] = None,
    db = Depends(get_db),
    admin = Depends(get_admin_user)
):
    qs_doc = db.question_sets.find_one({"id": set_id})
    if not qs_doc:
        raise HTTPException(status_code=404, detail="Question set not found")
    qs = to_mongo_doc(qs_doc)

    target_date_str = schedule_date or qs.schedule_date
    target_date = validate_schedule_date(target_date_str)

    qs_groups = db.questions.distinct("question_group_id", {"question_set_id": set_id})
    logical_q_count = len(qs_groups)

    if logical_q_count == 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot schedule an empty question set. Please add questions before scheduling."
        )

    existing = db.question_sets.find_one({
        "exam_id": qs.exam_id,
        "test_id": qs.test_id,
        "schedule_date": target_date_str,
        "status": {"$in": [QuestionSetStatus.SCHEDULED, QuestionSetStatus.ACTIVE]},
        "id": {"$ne": set_id}
    })

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"A question set '{existing['title']}' is already {existing['status']} for this test on {target_date_str}."
        )

    update_fields = {
        "schedule_date": target_date_str,
        "publish_at": get_ist_12pm_utc(target_date),
        "expire_at": get_ist_12pm_utc(target_date + timedelta(days=1)),
        "status": QuestionSetStatus.SCHEDULED,
        "question_count": logical_q_count,
        "updated_at": datetime.utcnow()
    }

    db.question_sets.update_one({"id": set_id}, {"$set": update_fields})
    updated_doc = db.question_sets.find_one({"id": set_id})
    updated_qs = to_mongo_doc(updated_doc)

    create_audit_log(
        db,
        action="QUESTION_SET_SCHEDULED",
        user_id=admin.id,
        question_set_id=set_id,
        details=f"Scheduled question set '{updated_qs.title}' for publication on {updated_qs.schedule_date} at 12:00 PM IST."
    )

    current_ist = get_current_ist_date()
    if target_date == current_ist:
        activate_daily_sets_transaction(db, target_date_str)
        updated_doc = db.question_sets.find_one({"id": set_id})
        updated_qs = to_mongo_doc(updated_doc)

    return format_question_set_out(db, updated_qs)

@router.post("/{set_id}/cancel", response_model=QuestionSetOut)
def cancel_question_set(
    set_id: int,
    db = Depends(get_db),
    admin = Depends(get_admin_user)
):
    qs_doc = db.question_sets.find_one({"id": set_id})
    if not qs_doc:
        raise HTTPException(status_code=404, detail="Question set not found")
    qs = to_mongo_doc(qs_doc)

    if qs.status == QuestionSetStatus.EXPIRED:
        raise HTTPException(status_code=400, detail="Cannot cancel an already expired question set.")

    db.question_sets.update_one(
        {"id": set_id},
        {"$set": {"status": QuestionSetStatus.CANCELLED, "updated_at": datetime.utcnow()}}
    )
    updated_doc = db.question_sets.find_one({"id": set_id})
    updated_qs = to_mongo_doc(updated_doc)

    create_audit_log(
        db,
        action="QUESTION_SET_CANCELLED",
        user_id=admin.id,
        question_set_id=set_id,
        details=f"Cancelled question set '{updated_qs.title}' (Date: {updated_qs.schedule_date})."
    )
    return format_question_set_out(db, updated_qs)

@router.post("/{set_id}/publish-now", response_model=QuestionSetOut)
def publish_question_set_now(
    set_id: int,
    db = Depends(get_db),
    admin = Depends(get_admin_user)
):
    qs_doc = db.question_sets.find_one({"id": set_id})
    if not qs_doc:
        raise HTTPException(status_code=404, detail="Question set not found")
    qs = to_mongo_doc(qs_doc)

    qs_groups = db.questions.distinct("question_group_id", {"question_set_id": set_id})
    logical_q_count = len(qs_groups)

    if logical_q_count == 0:
        raise HTTPException(status_code=400, detail="Cannot publish an empty question set.")

    now_utc = datetime.utcnow()

    active_sets_docs = list(db.question_sets.find({
        "exam_id": qs.exam_id,
        "test_id": qs.test_id,
        "status": QuestionSetStatus.ACTIVE,
        "id": {"$ne": set_id}
    }))

    for old_active in active_sets_docs:
        db.question_sets.update_one(
            {"id": old_active["id"]},
            {"$set": {"status": QuestionSetStatus.EXPIRED, "expired_at": now_utc}}
        )
        create_audit_log(
            db,
            action="QUESTION_SET_EXPIRED",
            user_id=admin.id,
            question_set_id=old_active["id"],
            details=f"Expired set '{old_active.get('title')}' due to manual publish of set #{set_id}."
        )

    db.question_sets.update_one(
        {"id": set_id},
        {"$set": {
            "status": QuestionSetStatus.ACTIVE,
            "published_at": now_utc,
            "question_count": logical_q_count,
            "updated_at": now_utc
        }}
    )

    create_audit_log(
        db,
        action="QUESTION_SET_PUBLISHED_MANUALLY",
        user_id=admin.id,
        question_set_id=set_id,
        details=f"Admin manually published question set '{qs.title}' immediately."
    )

    updated_doc = db.question_sets.find_one({"id": set_id})
    return format_question_set_out(db, to_mongo_doc(updated_doc))

@router.delete("/{set_id}")
def delete_question_set(
    set_id: int,
    db = Depends(get_db),
    admin = Depends(get_admin_user)
):
    qs_doc = db.question_sets.find_one({"id": set_id})
    if not qs_doc:
        raise HTTPException(status_code=404, detail="Question set not found")
    qs = to_mongo_doc(qs_doc)

    if qs.status in [QuestionSetStatus.ACTIVE, QuestionSetStatus.EXPIRED]:
        raise HTTPException(status_code=400, detail=f"Cannot delete a question set in {qs.status} status. Cancel it instead.")

    db.question_sets.delete_one({"id": set_id})
    return {"message": f"Question set #{set_id} deleted successfully."}

@router.get("/audit-logs/recent", response_model=List[AuditLogOut])
def get_recent_audit_logs(
    limit: int = 50,
    db = Depends(get_db),
    admin = Depends(get_admin_user)
):
    logs_docs = list(db.audit_logs.find({}, sort=[("id", DESCENDING)], limit=limit))
    return [to_mongo_doc(l) for l in logs_docs]
