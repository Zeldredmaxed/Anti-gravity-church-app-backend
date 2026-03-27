from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, exists
from datetime import datetime, timezone, timedelta
from app.database import get_db
from app.models.member import Member
from app.models.attendance import AttendanceRecord
from app.models.volunteer import VolunteerSchedule
from app.models.family import FamilyRelationship
from app.models.user import User
from app.schemas.communication import SegmentFilter, MessagePayload, MessageResponse
from app.utils.security import require_role
from app.schemas.member import MemberResponse

router = APIRouter(prefix="/communications", tags=["Communications"])


@router.post("/segment", response_model=list[MemberResponse])
async def build_segment(
    filter_in: SegmentFilter,
    current_user: User = Depends(require_role("admin", "pastor", "ministry_leader", "staff")),
    db: AsyncSession = Depends(get_db),
):
    """
    Smart Segmentation Engine. Evaluates dynamic JSON query filters to returning a list of Member objects.
    """
    query = select(Member).where(Member.church_id == current_user.church_id, Member.is_deleted == False)

    if filter_in.membership_status:
        query = query.where(Member.membership_status == filter_in.membership_status)

    if filter_in.gender:
        query = query.where(Member.gender == filter_in.gender)
        
    # Age logic (simplistic assuming date_of_birth is present)
    today = datetime.now(timezone.utc).date()
    if filter_in.min_age is not None:
        max_birth_date = today.replace(year=today.year - filter_in.min_age)
        query = query.where(Member.date_of_birth <= max_birth_date)
    if filter_in.max_age is not None:
        min_birth_date = today.replace(year=today.year - filter_in.max_age - 1)
        query = query.where(Member.date_of_birth > min_birth_date)

    if filter_in.is_serving is not None:
        if filter_in.is_serving:
            query = query.where(
                exists().where(
                    and_(
                        VolunteerSchedule.member_id == Member.id,
                        VolunteerSchedule.church_id == Member.church_id
                    )
                )
            )
        else:
            query = query.where(
                ~exists().where(
                    and_(
                        VolunteerSchedule.member_id == Member.id,
                        VolunteerSchedule.church_id == Member.church_id
                    )
                )
            )
            
    if filter_in.has_children is not None:
        if filter_in.has_children:
            # Simplistic check if they are in a family where relationship = "Parent"
            query = query.where(
                exists().where(
                    and_(
                        FamilyRelationship.member_id == Member.id,
                        FamilyRelationship.relationship_type.in_(["parent", "father", "mother"])
                    )
                )
            )

    if filter_in.not_attended_days is not None:
        cutoff_date = today - timedelta(days=filter_in.not_attended_days)
        # They do not have an attendance record after cutoff_date
        query = query.where(
            ~exists().where(
                and_(
                    AttendanceRecord.member_id == Member.id,
                    AttendanceRecord.date >= cutoff_date
                )
            )
        )

    result = await db.execute(query)
    members = result.scalars().all()
    return members


@router.post("/mass-message", response_model=MessageResponse)
async def send_mass_message(
    payload: MessagePayload,
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db),
):
    """
    Accepts a list of members and dispatches the payload via requested medium (SMS/Email/Push).
    In a production scenario, this hooks into Twilio, AWS SES, or Firebase.
    """
    if not payload.target_member_ids:
        raise HTTPException(status_code=400, detail="No members targeted for the message.")
        
    # TODO: Fetch valid members from target list
    query = select(Member).where(
        Member.id.in_(payload.target_member_ids),
        Member.church_id == current_user.church_id
    )
    result = await db.execute(query)
    members = result.scalars().all()
    
    # Mocking external API dispatch
    successfully_queued = len(members)
    
    return MessageResponse(
        status="sent",
        messages_queued=successfully_queued,
        failed_enqueued=len(payload.target_member_ids) - successfully_queued
    )
