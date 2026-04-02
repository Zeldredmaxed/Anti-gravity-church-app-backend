from typing import List, Optional, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.utils.security import get_current_user
from app.models.user import User
from app.models.support_tickets import SupportRequest, SupportReport, AbuseReport, TicketStatus, TicketPriority

router = APIRouter(prefix="/support", tags=["Support Center"])

class SupportRequestOut(BaseModel):
    id: int
    subject: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SupportReportCreate(BaseModel):
    category: str
    description: str
    device_info: Optional[dict] = None
    attachments: Optional[list] = None

class AbuseReportCreate(BaseModel):
    reported_username: str
    reason: str
    description: Optional[str] = None
    content_url: Optional[str] = None


@router.get("/requests", response_model=List[SupportRequestOut])
async def get_user_support_requests(
    status: Optional[TicketStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.member_id:
        raise HTTPException(status_code=400, detail="User is not a member.")
        
    query = select(SupportRequest).where(SupportRequest.user_id == current_user.member_id)
    if status:
        query = query.where(SupportRequest.status == status)
        
    res = await db.execute(query.order_by(SupportRequest.updated_at.desc()))
    return res.scalars().all()


@router.post("/reports", status_code=status.HTTP_201_CREATED)
async def create_support_report(
    report_in: SupportReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.member_id:
        raise HTTPException(status_code=400, detail="User is not a member.")
        
    new_report = SupportReport(
        user_id=current_user.member_id,
        category=report_in.category,
        description=report_in.description,
        device_info=report_in.device_info,
        attachments=report_in.attachments
    )
    db.add(new_report)
    await db.commit()
    await db.refresh(new_report)
    return {"message": "Support report created successfully.", "id": new_report.id}


@router.post("/abuse-reports", status_code=status.HTTP_201_CREATED)
async def create_abuse_report(
    report_in: AbuseReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.member_id:
        raise HTTPException(status_code=400, detail="User is not a member.")
        
    new_abuse_report = AbuseReport(
        reporter_id=current_user.member_id,
        reported_username=report_in.reported_username,
        reason=report_in.reason,
        description=report_in.description,
        content_url=report_in.content_url
    )
    db.add(new_abuse_report)
    await db.commit()
    await db.refresh(new_abuse_report)
    return {"message": "Abuse report created successfully.", "id": new_abuse_report.id}
