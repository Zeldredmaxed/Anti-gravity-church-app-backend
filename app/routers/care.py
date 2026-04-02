"""Care Cases router - handle tracking pastoral care cases with notes and notification actions."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict

from app.database import get_db
from app.models.care import CareCase, CareNote
from app.models.user import User
from app.schemas.care import CareCaseCreate, CareCaseUpdate, CareCaseResponse
from app.utils.security import get_current_user, require_role

router = APIRouter(prefix="/care", tags=["Pastoral Care"])

@router.get("", response_model=list[CareCaseResponse])
async def list_care_cases(
    status: str = Query(None),
    care_type: str = Query(None),
    assigned_leader_id: int = Query(None),
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db)
):
    query = select(CareCase).where(
        CareCase.church_id == current_user.church_id,
        CareCase.is_deleted == False
    )
    if status:
        query = query.where(CareCase.status == status)
    if care_type:
        query = query.where(CareCase.care_type == care_type)
    if assigned_leader_id is not None:
        query = query.where(CareCase.assigned_leader_id == assigned_leader_id)

    query = query.order_by(CareCase.created_at.desc())
    cases = (await db.execute(query)).scalars().all()
    
    items = []
    for c in cases:
        leader_name = None
        leader_avatar = None
        if c.assigned_leader_id:
            leader = (await db.execute(select(User).where(User.id == c.assigned_leader_id))).scalar_one_or_none()
            if leader:
                leader_name = leader.full_name
                leader_avatar = getattr(leader, "avatar_url", None)
        
        items.append(CareCaseResponse(
            id=c.id,
            church_id=c.church_id,
            requester_name=c.requester_name,
            requester_avatar=c.requester_avatar,
            care_type=c.care_type,
            sub_type=c.sub_type,
            summary=c.summary,
            status=c.status,
            assigned_leader_id=c.assigned_leader_id,
            assigned_leader_name=leader_name,
            assigned_leader_avatar=leader_avatar,
            created_at=c.created_at,
            updated_at=c.updated_at
        ))
    return items

@router.post("", response_model=CareCaseResponse, status_code=201)
async def create_care_case(
    data: CareCaseCreate,
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db)
):
    case = CareCase(
        church_id=current_user.church_id,
        **data.model_dump()
    )
    db.add(case)
    await db.commit()
    await db.refresh(case)
    
    leader_name = None
    leader_avatar = None
    if case.assigned_leader_id:
        leader = (await db.execute(select(User).where(User.id == case.assigned_leader_id))).scalar_one_or_none()
        if leader:
            leader_name = leader.full_name
            leader_avatar = getattr(leader, "avatar_url", None)

    return CareCaseResponse(
        id=case.id,
        church_id=case.church_id,
        requester_name=case.requester_name,
        requester_avatar=case.requester_avatar,
        care_type=case.care_type,
        sub_type=case.sub_type,
        summary=case.summary,
        status=case.status,
        assigned_leader_id=case.assigned_leader_id,
        assigned_leader_name=leader_name,
        assigned_leader_avatar=leader_avatar,
        created_at=case.created_at,
        updated_at=case.updated_at
    )

@router.put("/{case_id}", response_model=CareCaseResponse)
async def update_care_case(
    case_id: int,
    data: CareCaseUpdate,
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db)
):
    case = (await db.execute(select(CareCase).where(
        CareCase.id == case_id,
        CareCase.church_id == current_user.church_id
    ))).scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Care case not found")
        
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(case, field, value)
        
    db.add(case)
    await db.commit()
    await db.refresh(case)
    
    leader_name = None
    leader_avatar = None
    if case.assigned_leader_id:
        leader = (await db.execute(select(User).where(User.id == case.assigned_leader_id))).scalar_one_or_none()
        if leader:
            leader_name = leader.full_name
            leader_avatar = getattr(leader, "avatar_url", None)
            
    return CareCaseResponse(
        id=case.id,
        church_id=case.church_id,
        requester_name=case.requester_name,
        requester_avatar=case.requester_avatar,
        care_type=case.care_type,
        sub_type=case.sub_type,
        summary=case.summary,
        status=case.status,
        assigned_leader_id=case.assigned_leader_id,
        assigned_leader_name=leader_name,
        assigned_leader_avatar=leader_avatar,
        created_at=case.created_at,
        updated_at=case.updated_at
    )

@router.delete("/{case_id}", status_code=204)
async def delete_care_case(
    case_id: int,
    current_user: User = Depends(require_role("admin", "pastor")),
    db: AsyncSession = Depends(get_db)
):
    case = (await db.execute(select(CareCase).where(
        CareCase.id == case_id,
        CareCase.church_id == current_user.church_id
    ))).scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Care case not found")
        
    case.is_deleted = True
    db.add(case)
    await db.commit()


# ── Care Notes (Follow-up tracking) ──

class CareNoteCreate(BaseModel):
    content: str
    action_taken: Optional[str] = None  # "Phone Call", "Home Visit", "SMS Sent"


class CareNoteResponse(BaseModel):
    id: int
    care_case_id: int
    author_id: int
    content: str
    action_taken: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.get("/{case_id}/notes", response_model=list[CareNoteResponse])
async def list_care_notes(
    case_id: int,
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db),
):
    """Get all follow-up notes for a care case."""
    result = await db.execute(
        select(CareNote)
        .where(CareNote.care_case_id == case_id)
        .order_by(CareNote.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{case_id}/notes", response_model=CareNoteResponse, status_code=201)
async def add_care_note(
    case_id: int,
    data: CareNoteCreate,
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db),
):
    """Add a follow-up note to a care case."""
    case = (await db.execute(select(CareCase).where(
        CareCase.id == case_id, CareCase.church_id == current_user.church_id
    ))).scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Care case not found")

    note = CareNote(
        care_case_id=case_id,
        author_id=current_user.id,
        content=data.content,
        action_taken=data.action_taken,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


# ── Action Endpoints (SMS / Email) ──

class SendSMSRequest(BaseModel):
    phone_number: str
    message: str


class SendEmailRequest(BaseModel):
    email: str
    subject: str
    body: str


@router.post("/{case_id}/actions/send-sms")
async def send_sms_action(
    case_id: int,
    data: SendSMSRequest,
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db),
):
    """Send an SMS from the care case and log the action as a note."""
    case = (await db.execute(select(CareCase).where(
        CareCase.id == case_id, CareCase.church_id == current_user.church_id
    ))).scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Care case not found")

    from app.services.notification_service import send_sms
    result = await send_sms(to=data.phone_number, body=data.message)

    # Log as care note
    note = CareNote(
        care_case_id=case_id,
        author_id=current_user.id,
        content=f"SMS sent to {data.phone_number}: {data.message}",
        action_taken="SMS Sent",
    )
    db.add(note)
    await db.commit()

    return {"sms_result": result, "note_logged": True}


@router.post("/{case_id}/actions/send-email")
async def send_email_action(
    case_id: int,
    data: SendEmailRequest,
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db),
):
    """Send an email from the care case and log the action as a note."""
    case = (await db.execute(select(CareCase).where(
        CareCase.id == case_id, CareCase.church_id == current_user.church_id
    ))).scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Care case not found")

    from app.services.notification_service import send_email
    result = await send_email(to=data.email, subject=data.subject, html_body=data.body)

    # Log as care note
    note = CareNote(
        care_case_id=case_id,
        author_id=current_user.id,
        content=f"Email sent to {data.email}: {data.subject}",
        action_taken="Email Sent",
    )
    db.add(note)
    await db.commit()

    return {"email_result": result, "note_logged": True}
