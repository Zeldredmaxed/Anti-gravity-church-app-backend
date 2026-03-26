"""Support router — help & contact endpoints."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import get_db, Base
from app.models.user import User
from app.utils.security import get_current_user

router = APIRouter(prefix="/support", tags=["Support"])


# ── Model ─────────────────────────────────────────────────────────
class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    subject = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(20), default="open")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User")


# ── Schemas ───────────────────────────────────────────────────────
class ContactRequest(BaseModel):
    subject: str
    message: str


# ── Endpoints ─────────────────────────────────────────────────────

@router.get("/contact")
async def get_contact_info():
    """Return support contact information."""
    return {"data": {
        "email": "support@antigravitychurch.com",
        "phone": "(404) 000-0000",
        "hours": "Mon-Fri 9AM-5PM EST",
        "website": "https://antigravitychurch.com/support",
    }}


@router.post("/contact", status_code=201)
async def submit_support_request(
    data: ContactRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ticket = SupportTicket(
        user_id=current_user.id,
        subject=data.subject,
        message=data.message,
    )
    db.add(ticket)
    await db.flush()
    await db.refresh(ticket)
    return {"data": {"id": ticket.id, "status": "open", "message": "Your request has been submitted."}}
