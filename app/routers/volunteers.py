from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timezone

from app.database import get_db
from app.models.user import User
from app.models.volunteer import VolunteerRole, VolunteerSchedule, VolunteerAvailability
from pydantic import BaseModel, ConfigDict
from app.models.event import Event
from app.models.member import Member
from sqlalchemy.orm import joinedload


router = APIRouter(prefix="/volunteers", tags=["volunteers"])

class VolunteerRoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    teams: Optional[str] = None
    capacity_needed: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)

class VolunteerScheduleResponse(BaseModel):
    id: int
    role_id: int
    event_id: int
    user_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str
    
    model_config = ConfigDict(from_attributes=True)

class VolunteerListResponse(BaseModel):
    id: str
    name: str
    avatar: str
    role: Optional[str] = None
    available: bool = True
    team: Optional[str] = None
    contact: Optional[str] = None

@router.get("/roles", response_model=List[VolunteerRoleResponse])
def get_volunteer_roles(db: Session = Depends(get_db)):
    """Get all volunteer roles."""
    roles = db.query(VolunteerRole).filter(VolunteerRole.is_active == True).all()
    return roles

@router.get("/schedules", response_model=List[VolunteerScheduleResponse])
def get_volunteer_schedules(db: Session = Depends(get_db)):
    """Get upcoming volunteer schedules."""
    schedules = db.query(VolunteerSchedule).all()
    return schedules

@router.get("/list", response_model=List[VolunteerListResponse])
def get_volunteer_list(db: Session = Depends(get_db)):
    """Get a list of members who are volunteers (have schedules or roles)."""
    # Fetch members who have schedules
    schedules = db.query(VolunteerSchedule).options(
        joinedload(VolunteerSchedule.member),
        joinedload(VolunteerSchedule.role)
    ).all()
    
    volunteers_map = {}
    
    for s in schedules:
        m = s.member
        if not m:
            continue
            
        if str(m.id) not in volunteers_map:
            volunteers_map[str(m.id)] = {
                "id": str(m.id),
                "name": f"{m.first_name} {m.last_name}".strip(),
                "avatar": m.avatar_url or f"https://ui-avatars.com/api/?name={m.first_name}+{m.last_name}&background=random",
                "role": s.role.name if s.role else None,
                "available": True, # You would check VolunteerAvailability here
                "team": s.role.name if s.role else "General",
                "contact": m.email or m.phone or "N/A"
            }
            
    return list(volunteers_map.values())

@router.get("/metrics")
def get_volunteer_metrics(db: Session = Depends(get_db)):
    """Get aggregated metrics for the volunteers dashboard."""
    # Active Volunteers (users who have a role or schedule)
    active_schedules_count = db.query(func.count(VolunteerSchedule.user_id.distinct())).filter(
        VolunteerSchedule.status == "confirmed"
    ).scalar() or 0

    # Total Roles
    total_roles = db.query(VolunteerRole).filter(VolunteerRole.is_active == True).count()

    # Hours Served (Placeholder logic. E.g. assume each past schedule is 2 hours)
    now = datetime.now(timezone.utc)
    completed_schedules = db.query(VolunteerSchedule).filter(
        VolunteerSchedule.end_time < now,
        VolunteerSchedule.status == "confirmed"
    ).all()
    
    hours_served = 0
    for s in completed_schedules:
        if s.start_time and s.end_time:
            hours_served += (s.end_time - s.start_time).total_seconds() / 3600
        else:
            hours_served += 2

    return {
        "active_volunteers": active_schedules_count,
        "total_roles": total_roles,
        "hours_served": int(hours_served),
        "upcoming_needs": 5 # Placeholder
    }
