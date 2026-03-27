import asyncio
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, and_, exists
from app.database import async_session
from app.models.automation import AutomationRule
from app.models.member import Member
from app.models.attendance import AttendanceRecord

logger = logging.getLogger(__name__)

async def _process_missed_attendance_rule(rule: AutomationRule, session):
    """
    Find members who haven't attended in X days.
    """
    days = rule.trigger_conditions.get("days_missed", 14)
    cutoff_date = datetime.now(timezone.utc).date() - timedelta(days=days)
    
    # query members
    # 1. Active or Member status
    # 2. No attendance after cutoff_date
    
    query = select(Member).where(
        Member.church_id == rule.church_id,
        Member.is_deleted == False,
        Member.membership_status.in_(["active", "member"]),
        ~exists().where(
            and_(
                AttendanceRecord.member_id == Member.id,
                AttendanceRecord.date >= cutoff_date
            )
        )
    )
    result = await session.execute(query)
    members = result.scalars().all()
    
    for member in members:
        # Execute action
        logger.info(f"Would trigger {rule.action_type} for member {member.id} via rule {rule.id}")
        
    
    await session.commit()

async def automation_task_runner():
    """
    Background loop that wakes up periodically and checks active automation rules.
    """
    while True:
        try:
            async with async_session() as session:
                active_rules_query = select(AutomationRule).where(AutomationRule.is_active == True)
                result = await session.execute(active_rules_query)
                rules = result.scalars().all()
                
                for rule in rules:
                    if rule.trigger_type == "missed_attendance":
                        await _process_missed_attendance_rule(rule, session)
                    elif rule.trigger_type == "first_time_visitor":
                        # Similar logic for new visitors
                        pass
                    elif rule.trigger_type == "birthday":
                        # Check birthdays
                        pass
        except Exception as e:
            logger.error(f"Error in automation runner: {e}")
            
        # Sleep for an hour
        await asyncio.sleep(3600)
