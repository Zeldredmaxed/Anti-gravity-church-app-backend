from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone

from app.database import get_db
from app.models.member import Member
from app.models.donation import Donation
from app.models.attendance import AttendanceRecord
from app.models.group import Group
from app.models.event import Event
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/metrics")
def get_dashboard_metrics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get aggregated metrics for the dashboard view."""
    # This could be scoped by church_id if multitenancy is fully implemented.
    # We will assume a single church for now or fetch based on current_user.church_id if exists.
    church_id_filter = True # Placeholder for actual church_id filtering
    try:
        church_id = current_user.church_id
        if church_id:
            church_id_filter = Member.church_id == church_id
    except AttributeError:
        pass # If current_user doesn't have church_id, just continue

    # Members Count
    total_members = db.query(Member).filter(church_id_filter).count()

    # Active Groups
    total_groups = db.query(Group).count() # Apply church_id filter as needed
    
    # Total Giving (Current Month)
    now = datetime.now(timezone.utc)
    first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    total_giving_query = db.query(func.sum(Donation.amount)).filter(
        Donation.status == 'completed',
        Donation.created_at >= first_day_of_month
    ).scalar()
    
    total_giving = total_giving_query if total_giving_query else 0.0

    # Total Attendance (Last 30 Days)
    thirty_days_ago = now - timedelta(days=30)
    attendance_count = db.query(func.count(AttendanceRecord.id)).filter(
        AttendanceRecord.timestamp >= thirty_days_ago,
        AttendanceRecord.status == 'present'
    ).scalar()

    return {
        "giving": {
            "total": float(total_giving),
            "trend": 15 # Placeholder trend %
        },
        "attendance": {
            "total": attendance_count or 0,
            "trend": 5
        },
        "groups": {
            "total": total_groups,
            "trend": 2 # 2 new this month
        },
        "members": {
            "total": total_members,
            "trend": 10
        }
    }

@router.get("/events")
def get_dashboard_events(limit: int = 5, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get upcoming events for the dashboard."""
    now = datetime.now(timezone.utc)
    events = db.query(Event).filter(
        Event.start_time >= now
    ).order_by(Event.start_time.asc()).limit(limit).all()
    
    return [
        {
            "id": e.id,
            "title": e.title,
            "date": e.start_time.isoformat() if e.start_time else None,
            "location": e.location
        }
        for e in events
    ]

@router.get("/activity")
def get_dashboard_activity(limit: int = 5, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get recent church activity feed."""
    # In a real app this would query an ActivityLog or AuditLog table.
    # For now, returning mock data that aligns with the UI needs.
    return [
        {"id": 1, "action": "Alex Rivera joined", "target": "Youth Ministry", "time": "2 hours ago"},
        {"id": 2, "action": "Sarah Jenkins registered", "target": "Marriage Retreat", "time": "5 hours ago"},
        {"id": 3, "action": "David Lee made a", "target": "First-time Donation", "time": "1 day ago"}
    ]
