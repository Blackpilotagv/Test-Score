from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime, date, timedelta

from app.database.session import get_db
from app.models.models import User, Exam, Test, Question, QuestionSet, QuestionSetStatus, AuditLog
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

def format_question_set_out(qs: QuestionSet) -> QuestionSetOut:
    """Helper to convert QuestionSet DB model to QuestionSetOut Pydantic model with relationships."""
    exam_name = qs.exam.name if qs.exam else ""
    exam_slug = qs.exam.slug if qs.exam else ""
    test_title = qs.test.title if qs.test else ""
    
    # Calculate logical question count if 0
    q_count = qs.question_count
    if q_count == 0 and qs.questions:
        q_count = len(set(q.question_group_id for q in qs.questions))

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
        status=qs.status.value if hasattr(qs.status, "value") else str(qs.status),
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
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    query = db.query(QuestionSet)
    if exam_id:
        query = query.filter(QuestionSet.exam_id == exam_id)
    if test_id:
        query = query.filter(QuestionSet.test_id == test_id)
    if status_str:
        query = query.filter(QuestionSet.status == QuestionSetStatus(status_str.upper()))
    if schedule_date:
        query = query.filter(QuestionSet.schedule_date == schedule_date)

    sets = query.order_by(QuestionSet.schedule_date.desc(), QuestionSet.id.desc()).all()
    return [format_question_set_out(s) for s in sets]

@router.get("/calendar", response_model=List[SchedulerCalendarDay])
def get_7day_rolling_calendar(
    start_date: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    Returns a 7-day rolling schedule grid for week view.
    Default starts at current IST date and projects 7 days ahead.
    """
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

        sets_for_day = db.query(QuestionSet).filter(QuestionSet.schedule_date == day_str).all()
        formatted_sets = [format_question_set_out(s) for s in sets_for_day]

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
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    exam = db.query(Exam).filter(Exam.id == qs_in.exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam category not found")

    test = db.query(Test).filter(Test.id == qs_in.test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Daily test not found")

    # Validate schedule date horizon (0 to 7 days ahead)
    target_date = validate_schedule_date(qs_in.schedule_date)

    # Check for existing active or scheduled QuestionSet on the same date for this test
    existing = db.query(QuestionSet).filter(
        QuestionSet.exam_id == qs_in.exam_id,
        QuestionSet.test_id == qs_in.test_id,
        QuestionSet.schedule_date == qs_in.schedule_date,
        QuestionSet.status.in_([QuestionSetStatus.SCHEDULED, QuestionSetStatus.ACTIVE])
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"A question set '{existing.title}' is already {existing.status.value} for this test on {qs_in.schedule_date}."
        )

    publish_utc = get_ist_12pm_utc(target_date)
    expire_utc = get_ist_12pm_utc(target_date + timedelta(days=1))

    new_set = QuestionSet(
        exam_id=qs_in.exam_id,
        test_id=qs_in.test_id,
        title=qs_in.title,
        schedule_date=qs_in.schedule_date,
        publish_at=publish_utc,
        expire_at=expire_utc,
        status=QuestionSetStatus(qs_in.status.upper()) if qs_in.status else QuestionSetStatus.DRAFT,
        created_by=admin.id,
        created_at=datetime.utcnow()
    )

    db.add(new_set)
    db.commit()
    db.refresh(new_set)

    create_audit_log(
        db,
        action="QUESTION_SET_CREATED",
        user_id=admin.id,
        question_set_id=new_set.id,
        details=f"Created question set '{new_set.title}' for date {new_set.schedule_date}."
    )
    db.commit()

    return format_question_set_out(new_set)

@router.get("/{set_id}", response_model=QuestionSetOut)
def get_question_set_detail(
    set_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    qs = db.query(QuestionSet).filter(QuestionSet.id == set_id).first()
    if not qs:
        raise HTTPException(status_code=404, detail="Question set not found")
    return format_question_set_out(qs)

@router.put("/{set_id}", response_model=QuestionSetOut)
def update_question_set(
    set_id: int,
    qs_in: QuestionSetUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    qs = db.query(QuestionSet).filter(QuestionSet.id == set_id).first()
    if not qs:
        raise HTTPException(status_code=404, detail="Question set not found")

    if qs.status in [QuestionSetStatus.ACTIVE, QuestionSetStatus.EXPIRED]:
        raise HTTPException(status_code=400, detail=f"Cannot edit a question set in {qs.status.value} status.")

    if qs_in.schedule_date and qs_in.schedule_date != qs.schedule_date:
        target_date = validate_schedule_date(qs_in.schedule_date)
        
        # Check duplicate
        existing = db.query(QuestionSet).filter(
            QuestionSet.exam_id == qs.exam_id,
            QuestionSet.test_id == qs.test_id,
            QuestionSet.schedule_date == qs_in.schedule_date,
            QuestionSet.status.in_([QuestionSetStatus.SCHEDULED, QuestionSetStatus.ACTIVE]),
            QuestionSet.id != set_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"A question set is already scheduled for this test on {qs_in.schedule_date}."
            )

        qs.schedule_date = qs_in.schedule_date
        qs.publish_at = get_ist_12pm_utc(target_date)
        qs.expire_at = get_ist_12pm_utc(target_date + timedelta(days=1))

    if qs_in.title:
        qs.title = qs_in.title

    if qs_in.status:
        qs.status = QuestionSetStatus(qs_in.status.upper())

    qs.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(qs)

    create_audit_log(
        db,
        action="QUESTION_SET_UPDATED",
        user_id=admin.id,
        question_set_id=qs.id,
        details=f"Updated question set #{qs.id} title='{qs.title}', date={qs.schedule_date}."
    )
    db.commit()

    return format_question_set_out(qs)

@router.post("/{set_id}/schedule", response_model=QuestionSetOut)
def schedule_question_set(
    set_id: int,
    schedule_date: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    qs = db.query(QuestionSet).filter(QuestionSet.id == set_id).first()
    if not qs:
        raise HTTPException(status_code=404, detail="Question set not found")

    target_date_str = schedule_date or qs.schedule_date
    target_date = validate_schedule_date(target_date_str)

    # Verify set has questions
    logical_q_count = db.query(func.count(func.distinct(Question.question_group_id))).filter(
        Question.question_set_id == set_id
    ).scalar() or 0

    if logical_q_count == 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot schedule an empty question set. Please add questions before scheduling."
        )

    # Check duplicate
    existing = db.query(QuestionSet).filter(
        QuestionSet.exam_id == qs.exam_id,
        QuestionSet.test_id == qs.test_id,
        QuestionSet.schedule_date == target_date_str,
        QuestionSet.status.in_([QuestionSetStatus.SCHEDULED, QuestionSetStatus.ACTIVE]),
        QuestionSet.id != set_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"A question set '{existing.title}' is already {existing.status.value} for this test on {target_date_str}."
        )

    qs.schedule_date = target_date_str
    qs.publish_at = get_ist_12pm_utc(target_date)
    qs.expire_at = get_ist_12pm_utc(target_date + timedelta(days=1))
    qs.status = QuestionSetStatus.SCHEDULED
    qs.question_count = logical_q_count
    qs.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(qs)

    create_audit_log(
        db,
        action="QUESTION_SET_SCHEDULED",
        user_id=admin.id,
        question_set_id=qs.id,
        details=f"Scheduled question set '{qs.title}' for publication on {qs.schedule_date} at 12:00 PM IST."
    )
    db.commit()

    # If scheduled date is today and time has passed 12 PM IST, execute instant activation catch-up
    current_ist = get_current_ist_date()
    if target_date == current_ist:
        activate_daily_sets_transaction(db, target_date_str)
        db.refresh(qs)

    return format_question_set_out(qs)

@router.post("/{set_id}/cancel", response_model=QuestionSetOut)
def cancel_question_set(
    set_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    qs = db.query(QuestionSet).filter(QuestionSet.id == set_id).first()
    if not qs:
        raise HTTPException(status_code=404, detail="Question set not found")

    if qs.status == QuestionSetStatus.EXPIRED:
        raise HTTPException(status_code=400, detail="Cannot cancel an already expired question set.")

    qs.status = QuestionSetStatus.CANCELLED
    qs.updated_at = datetime.utcnow()

    create_audit_log(
        db,
        action="QUESTION_SET_CANCELLED",
        user_id=admin.id,
        question_set_id=qs.id,
        details=f"Cancelled question set '{qs.title}' (Date: {qs.schedule_date})."
    )
    db.commit()
    db.refresh(qs)
    return format_question_set_out(qs)

@router.post("/{set_id}/publish-now", response_model=QuestionSetOut)
def publish_question_set_now(
    set_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    Immediate manual activation override by Admin.
    1. Safely expires any currently ACTIVE question set for the same exam & test.
    2. Activates the target question set immediately.
    """
    qs = db.query(QuestionSet).filter(QuestionSet.id == set_id).first()
    if not qs:
        raise HTTPException(status_code=404, detail="Question set not found")

    logical_q_count = db.query(func.count(func.distinct(Question.question_group_id))).filter(
        Question.question_set_id == set_id
    ).scalar() or 0

    if logical_q_count == 0:
        raise HTTPException(status_code=400, detail="Cannot publish an empty question set.")

    now_utc = datetime.utcnow()

    # Expire existing active sets for this test
    active_sets = db.query(QuestionSet).filter(
        QuestionSet.exam_id == qs.exam_id,
        QuestionSet.test_id == qs.test_id,
        QuestionSet.status == QuestionSetStatus.ACTIVE,
        QuestionSet.id != set_id
    ).all()

    for old_active in active_sets:
        old_active.status = QuestionSetStatus.EXPIRED
        old_active.expired_at = now_utc
        create_audit_log(
            db,
            action="QUESTION_SET_EXPIRED",
            user_id=admin.id,
            question_set_id=old_active.id,
            details=f"Expired set '{old_active.title}' due to manual publish of set #{qs.id}."
        )

    qs.status = QuestionSetStatus.ACTIVE
    qs.published_at = now_utc
    qs.question_count = logical_q_count
    qs.updated_at = now_utc

    create_audit_log(
        db,
        action="QUESTION_SET_PUBLISHED_MANUALLY",
        user_id=admin.id,
        question_set_id=qs.id,
        details=f"Admin manually published question set '{qs.title}' immediately."
    )

    db.commit()
    db.refresh(qs)
    return format_question_set_out(qs)

@router.delete("/{set_id}")
def delete_question_set(
    set_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    qs = db.query(QuestionSet).filter(QuestionSet.id == set_id).first()
    if not qs:
        raise HTTPException(status_code=404, detail="Question set not found")

    if qs.status in [QuestionSetStatus.ACTIVE, QuestionSetStatus.EXPIRED]:
        raise HTTPException(status_code=400, detail=f"Cannot delete a question set in {qs.status.value} status. Cancel it instead.")

    db.delete(qs)
    db.commit()
    return {"message": f"Question set #{set_id} deleted successfully."}

@router.get("/audit-logs/recent", response_model=List[AuditLogOut])
def get_recent_audit_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(limit).all()
    return logs
