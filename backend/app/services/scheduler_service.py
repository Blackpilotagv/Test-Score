import logging
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database.session import SessionLocal
from app.models.models import QuestionSet, QuestionSetStatus, AuditLog, Question, Test

logger = logging.getLogger("scheduler")
logger.setLevel(logging.INFO)

IST_TIMEZONE = ZoneInfo("Asia/Kolkata")

def get_current_ist_datetime() -> datetime:
    """Returns the current date & time in Asia/Kolkata timezone."""
    return datetime.now(IST_TIMEZONE)

def get_current_ist_date() -> date:
    """Returns the current date in Asia/Kolkata timezone."""
    return get_current_ist_datetime().date()

def get_current_ist_date_str() -> str:
    """Returns current IST date formatted as YYYY-MM-DD."""
    return get_current_ist_date().strftime("%Y-%m-%d")

def get_ist_12pm_utc(schedule_date: date) -> datetime:
    """Converts 12:00:00 PM IST on schedule_date into a UTC datetime for DB storage."""
    ist_dt = datetime.combine(schedule_date, datetime.min.time().replace(hour=12, minute=0, second=0)).replace(tzinfo=IST_TIMEZONE)
    return ist_dt.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

def validate_schedule_date(schedule_date_str: str) -> date:
    """
    Validates that schedule_date_str is in YYYY-MM-DD format,
    is not in the past, and does not exceed the 7-day rolling horizon.
    """
    try:
        target_date = datetime.strptime(schedule_date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Invalid date format. Expected YYYY-MM-DD.")

    current_ist = get_current_ist_date()
    max_allowed = current_ist + timedelta(days=7)

    if target_date < current_ist:
        raise ValueError(f"Cannot schedule for past date '{schedule_date_str}'. Today (IST) is {current_ist}.")

    if target_date > max_allowed:
        raise ValueError(
            f"Scheduling horizon exceeded. Date '{schedule_date_str}' is beyond the 7-day limit (Max allowed: {max_allowed})."
        )

    return target_date

def create_audit_log(db: Session, action: str, user_id: Optional[int] = None, question_set_id: Optional[int] = None, details: Optional[str] = None):
    """Creates a persistent audit log entry for scheduler & admin actions."""
    log = AuditLog(
        user_id=user_id,
        action=action,
        question_set_id=question_set_id,
        details=details,
        created_at=datetime.utcnow()
    )
    db.add(log)

def activate_daily_sets_transaction(db: Session, target_date_str: Optional[str] = None) -> Dict[str, Any]:
    """
    Atomic & Idempotent daily status transition:
    1. Expire currently ACTIVE QuestionSets whose schedule_date is older than target_date_str,
       or whenever today's SCHEDULED set is ready to activate for the same test.
    2. Activate SCHEDULED QuestionSets for target_date_str.
    3. Update published_at / expired_at timestamps.
    4. Log audit events.
    5. NEVER delete expired questions or historical attempts.
    """
    if not target_date_str:
        target_date_str = get_current_ist_date_str()

    now_utc = datetime.utcnow()
    expired_ids = []
    activated_ids = []

    try:
        # Find scheduled sets for target date or earlier that need activation
        scheduled_sets = db.query(QuestionSet).filter(
            QuestionSet.status == QuestionSetStatus.SCHEDULED,
            QuestionSet.schedule_date <= target_date_str
        ).order_by(QuestionSet.schedule_date.asc(), QuestionSet.id.asc()).all()

        for s_set in scheduled_sets:
            # Check for existing ACTIVE sets for the same exam & test
            active_sets = db.query(QuestionSet).filter(
                QuestionSet.exam_id == s_set.exam_id,
                QuestionSet.test_id == s_set.test_id,
                QuestionSet.status == QuestionSetStatus.ACTIVE,
                QuestionSet.id != s_set.id
            ).all()

            for old_active in active_sets:
                old_active.status = QuestionSetStatus.EXPIRED
                old_active.expired_at = now_utc
                expired_ids.append(old_active.id)
                create_audit_log(
                    db,
                    action="QUESTION_SET_EXPIRED",
                    question_set_id=old_active.id,
                    details=f"Expired set '{old_active.title}' (Date: {old_active.schedule_date}) upon activation of set #{s_set.id}."
                )

            # Activate the scheduled set
            s_set.status = QuestionSetStatus.ACTIVE
            s_set.published_at = now_utc
            activated_ids.append(s_set.id)
            create_audit_log(
                db,
                action="QUESTION_SET_ACTIVATED",
                question_set_id=s_set.id,
                details=f"Activated question set '{s_set.title}' for date {s_set.schedule_date} at 12:00 PM IST."
            )

        # Expire any orphaned ACTIVE sets whose schedule date is older than today
        outdated_active_sets = db.query(QuestionSet).filter(
            QuestionSet.status == QuestionSetStatus.ACTIVE,
            QuestionSet.schedule_date < target_date_str
        ).all()

        for out_set in outdated_active_sets:
            if out_set.id not in expired_ids:
                out_set.status = QuestionSetStatus.EXPIRED
                out_set.expired_at = now_utc
                expired_ids.append(out_set.id)
                create_audit_log(
                    db,
                    action="QUESTION_SET_EXPIRED",
                    question_set_id=out_set.id,
                    details=f"Expired outdated active set '{out_set.title}' (Date: {out_set.schedule_date})."
                )

        db.commit()
        logger.info(f"[Daily Scheduler] Activated sets: {activated_ids}, Expired sets: {expired_ids} for date {target_date_str}")
        return {
            "status": "success",
            "target_date": target_date_str,
            "activated_count": len(activated_ids),
            "activated_ids": activated_ids,
            "expired_count": len(expired_ids),
            "expired_ids": expired_ids
        }
    except Exception as e:
        db.rollback()
        logger.error(f"[Daily Scheduler Error] Transaction failed: {str(e)}")
        raise e

def reconcile_daily_question_sets(db: Session) -> Dict[str, Any]:
    """
    Executes on application startup to handle recovery from server restarts/downtime.
    Catches up missed 12:00 PM IST transitions safely and idempotently.
    """
    logger.info("[Daily Scheduler] Running server-restart reconciliation check...")
    res = activate_daily_sets_transaction(db, target_date_str=get_current_ist_date_str())
    create_audit_log(
        db,
        action="QUESTION_SET_SCHEDULER_RECOVERY",
        details=f"Server startup reconciliation completed. Activated: {res['activated_count']}, Expired: {res['expired_count']}."
    )
    db.commit()
    return res

# Global Scheduler Instance
app_scheduler = BackgroundScheduler(timezone=IST_TIMEZONE)

def _run_scheduled_job():
    """Job handler called by APScheduler every day at 12:00:00 PM IST."""
    logger.info("[Daily Scheduler Cron] Triggering 12:00 PM IST daily transition job...")
    db = SessionLocal()
    try:
        activate_daily_sets_transaction(db)
    finally:
        db.close()

def start_scheduler():
    """Starts the background APScheduler cron for daily 12:00 PM IST execution."""
    if not app_scheduler.running:
        # Schedule cron at 12:00 PM Asia/Kolkata
        app_scheduler.add_job(
            _run_scheduled_job,
            trigger=CronTrigger(hour=12, minute=0, second=0, timezone=IST_TIMEZONE),
            id="daily_question_set_activation",
            name="Daily 12:00 PM IST Question Set Activation",
            replace_existing=True
        )
        app_scheduler.start()
        logger.info("[Daily Scheduler] Background scheduler initialized and started successfully (12:00 PM IST cron).")
