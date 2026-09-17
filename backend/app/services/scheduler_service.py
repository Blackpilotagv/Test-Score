import logging
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from typing import List, Dict, Any, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database.session import get_mongo_db, get_next_sequence
from app.models.models import QuestionSetStatus, to_mongo_doc

logger = logging.getLogger("scheduler")
logger.setLevel(logging.INFO)

IST_TIMEZONE = ZoneInfo("Asia/Kolkata")

def get_current_ist_datetime() -> datetime:
    return datetime.now(IST_TIMEZONE)

def get_current_ist_date() -> date:
    return get_current_ist_datetime().date()

def get_current_ist_date_str() -> str:
    return get_current_ist_date().strftime("%Y-%m-%d")

def get_ist_12pm_utc(schedule_date: date) -> datetime:
    ist_dt = datetime.combine(schedule_date, datetime.min.time().replace(hour=12, minute=0, second=0)).replace(tzinfo=IST_TIMEZONE)
    return ist_dt.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

def validate_schedule_date(schedule_date_str: str) -> date:
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

def create_audit_log(db, action: str, user_id: Optional[int] = None, question_set_id: Optional[int] = None, details: Optional[str] = None):
    log_id = get_next_sequence(db, "audit_log_id")
    db.audit_logs.insert_one({
        "id": log_id,
        "user_id": user_id,
        "action": action,
        "question_set_id": question_set_id,
        "details": details,
        "created_at": datetime.utcnow()
    })

def activate_daily_sets_transaction(db, target_date_str: Optional[str] = None) -> Dict[str, Any]:
    if not target_date_str:
        target_date_str = get_current_ist_date_str()

    now_utc = datetime.utcnow()
    expired_ids = []
    activated_ids = []

    try:
        scheduled_sets_docs = list(db.question_sets.find(
            {"status": QuestionSetStatus.SCHEDULED, "schedule_date": {"$lte": target_date_str}},
            sort=[("schedule_date", 1), ("id", 1)]
        ))

        for s_doc in scheduled_sets_docs:
            s_set = to_mongo_doc(s_doc)
            active_sets_docs = list(db.question_sets.find({
                "exam_id": s_set.exam_id,
                "test_id": s_set.test_id,
                "status": QuestionSetStatus.ACTIVE,
                "id": {"$ne": s_set.id}
            }))

            for old_active in active_sets_docs:
                db.question_sets.update_one(
                    {"id": old_active["id"]},
                    {"$set": {"status": QuestionSetStatus.EXPIRED, "expired_at": now_utc}}
                )
                expired_ids.append(old_active["id"])
                create_audit_log(
                    db,
                    action="QUESTION_SET_EXPIRED",
                    question_set_id=old_active["id"],
                    details=f"Expired set '{old_active.get('title')}' (Date: {old_active.get('schedule_date')}) upon activation of set #{s_set.id}."
                )

            db.question_sets.update_one(
                {"id": s_set.id},
                {"$set": {"status": QuestionSetStatus.ACTIVE, "published_at": now_utc}}
            )
            activated_ids.append(s_set.id)
            create_audit_log(
                db,
                action="QUESTION_SET_ACTIVATED",
                question_set_id=s_set.id,
                details=f"Activated question set '{s_set.title}' for date {s_set.schedule_date} at 12:00 PM IST."
            )

        outdated_active_docs = list(db.question_sets.find({
            "status": QuestionSetStatus.ACTIVE,
            "schedule_date": {"$lt": target_date_str}
        }))

        for out_doc in outdated_active_docs:
            if out_doc["id"] not in expired_ids:
                db.question_sets.update_one(
                    {"id": out_doc["id"]},
                    {"$set": {"status": QuestionSetStatus.EXPIRED, "expired_at": now_utc}}
                )
                expired_ids.append(out_doc["id"])
                create_audit_log(
                    db,
                    action="QUESTION_SET_EXPIRED",
                    question_set_id=out_doc["id"],
                    details=f"Expired outdated active set '{out_doc.get('title')}' (Date: {out_doc.get('schedule_date')})."
                )

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
        logger.error(f"[Daily Scheduler Error] Transaction failed: {str(e)}")
        raise e

def reconcile_daily_question_sets(db) -> Dict[str, Any]:
    logger.info("[Daily Scheduler] Running server-restart reconciliation check...")
    res = activate_daily_sets_transaction(db, target_date_str=get_current_ist_date_str())
    create_audit_log(
        db,
        action="QUESTION_SET_SCHEDULER_RECOVERY",
        details=f"Server startup reconciliation completed. Activated: {res['activated_count']}, Expired: {res['expired_count']}."
    )
    return res

app_scheduler = BackgroundScheduler(timezone=IST_TIMEZONE)

def _run_scheduled_job():
    logger.info("[Daily Scheduler Cron] Triggering 12:00 PM IST daily transition job...")
    db = get_mongo_db()
    try:
        activate_daily_sets_transaction(db)
    except Exception as e:
        logger.error(f"Error during scheduled job execution: {e}")

def start_scheduler():
    if not app_scheduler.running:
        app_scheduler.add_job(
            _run_scheduled_job,
            trigger=CronTrigger(hour=12, minute=0, second=0, timezone=IST_TIMEZONE),
            id="daily_question_set_activation",
            name="Daily 12:00 PM IST Question Set Activation",
            replace_existing=True
        )
        app_scheduler.start()
        logger.info("[Daily Scheduler] Background scheduler initialized and started successfully (12:00 PM IST cron).")
