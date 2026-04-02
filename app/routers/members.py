"""Member management router: CRUD, notes, import/export, engagement."""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from typing import Optional
from datetime import datetime, timezone, date, timedelta
import csv
import io

from app.database import get_db
from app.models.member import Member, MemberNote
from app.models.user import User, UserRole
from app.models.donation import Donation
from app.models.attendance import AttendanceRecord
from app.models.group import GroupMembership
from app.schemas.member import (
    MemberCreate, MemberUpdate, MemberResponse, MemberListResponse,
    MemberNoteCreate, MemberNoteResponse, EngagementScore,
)
from app.utils.security import get_current_user, require_role, get_church_id
from app.dependencies import PaginationParams

router = APIRouter(prefix="/members", tags=["Members"])


@router.get("", response_model=MemberListResponse)
async def list_members(
    search: Optional[str] = Query(None, description="Search by name, email, or phone"),
    membership_status: Optional[str] = Query(None),
    family_id: Optional[int] = Query(None),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List members with search and filters."""
    query = select(Member).where(Member.church_id == current_user.church_id, Member.is_deleted == False)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Member.first_name.ilike(search_term),
                Member.last_name.ilike(search_term),
                Member.email.ilike(search_term),
                Member.phone.ilike(search_term),
            )
        )
    if membership_status:
        query = query.where(Member.membership_status == membership_status)
    if family_id:
        query = query.where(Member.family_id == family_id)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = query.order_by(Member.last_name, Member.first_name)
    query = query.offset(pagination.offset).limit(pagination.per_page)
    result = await db.execute(query)
    members = result.scalars().all()

    return MemberListResponse(
        items=[MemberResponse.model_validate(m) for m in members],
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        pages=(total + pagination.per_page - 1) // pagination.per_page,
    )


@router.post("", response_model=MemberResponse, status_code=201)
async def create_member(
    data: MemberCreate,
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new member profile."""
    member = Member(**data.model_dump(), church_id=current_user.church_id, created_by=current_user.id)
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


@router.get("/{member_id}", response_model=MemberResponse)
async def get_member(
    member_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a member by ID."""
    result = await db.execute(
        select(Member).where(Member.id == member_id, Member.church_id == current_user.church_id, Member.is_deleted == False)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


@router.put("/{member_id}", response_model=MemberResponse)
async def update_member(
    member_id: int,
    data: MemberUpdate,
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db),
):
    """Update a member profile."""
    result = await db.execute(
        select(Member).where(Member.id == member_id, Member.church_id == current_user.church_id, Member.is_deleted == False)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(member, field, value)

    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


@router.delete("/{member_id}", status_code=204)
async def delete_member(
    member_id: int,
    current_user: User = Depends(require_role("admin", "pastor")),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a member."""
    result = await db.execute(
        select(Member).where(Member.id == member_id, Member.church_id == current_user.church_id, Member.is_deleted == False)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    member.is_deleted = True
    db.add(member)


# --- Notes ---

@router.post("/{member_id}/notes", response_model=MemberNoteResponse, status_code=201)
async def add_note(
    member_id: int,
    data: MemberNoteCreate,
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db),
):
    """Add a note to a member's profile."""
    result = await db.execute(
        select(Member).where(Member.id == member_id, Member.is_deleted == False)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Member not found")

    note = MemberNote(
        member_id=member_id,
        author_id=current_user.id,
        note_type=data.note_type,
        content=data.content,
        is_confidential=data.is_confidential,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


@router.get("/{member_id}/notes", response_model=list[MemberNoteResponse])
async def get_notes(
    member_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get notes for a member (confidential notes require pastor/admin)."""
    query = select(MemberNote).where(MemberNote.member_id == member_id)

    # Non-pastor/admin can't see confidential notes
    if current_user.role not in ("admin", "pastor"):
        query = query.where(MemberNote.is_confidential == False)

    query = query.order_by(MemberNote.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


# --- Import/Export ---

@router.get("/export/csv")
async def export_members_csv(
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db),
):
    """Export all members as CSV."""
    result = await db.execute(
        select(Member).where(Member.church_id == current_user.church_id, Member.is_deleted == False).order_by(Member.last_name)
    )
    members = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "First Name", "Last Name", "Email", "Phone", "Address",
        "City", "State", "Zip", "DOB", "Gender", "Membership Status",
        "Join Date", "Baptism Date", "Baptism Type", "Salvation Date",
    ])
    for m in members:
        writer.writerow([
            m.id, m.first_name, m.last_name, m.email, m.phone, m.address,
            m.city, m.state, m.zip_code,
            m.date_of_birth.isoformat() if m.date_of_birth else "",
            m.gender, m.membership_status,
            m.join_date.isoformat() if m.join_date else "",
            m.baptism_date.isoformat() if m.baptism_date else "",
            m.baptism_type,
            m.salvation_date.isoformat() if m.salvation_date else "",
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=members_export.csv"},
    )


@router.post("/import/csv", status_code=201)
async def import_members_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role("admin", "pastor")),
    db: AsyncSession = Depends(get_db),
):
    """Import members from CSV file."""
    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode()))

    imported = 0
    errors = []

    for i, row in enumerate(reader, 1):
        try:
            member = Member(
                church_id=current_user.church_id,
                first_name=row.get("First Name", row.get("first_name", "")),
                last_name=row.get("Last Name", row.get("last_name", "")),
                email=row.get("Email", row.get("email")) or None,
                phone=row.get("Phone", row.get("phone")) or None,
                address=row.get("Address", row.get("address")) or None,
                city=row.get("City", row.get("city")) or None,
                state=row.get("State", row.get("state")) or None,
                zip_code=row.get("Zip", row.get("zip_code")) or None,
                gender=row.get("Gender", row.get("gender")) or None,
                membership_status=row.get("Membership Status", row.get("membership_status", "visitor")),
                created_by=current_user.id,
            )
            db.add(member)
            imported += 1
        except Exception as e:
            errors.append({"row": i, "error": str(e)})

    await db.commit()

    return {"imported": imported, "errors": errors}


# --- Engagement ---

@router.get("/{member_id}/engagement", response_model=EngagementScore)
async def get_engagement(
    member_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Calculate engagement score for a member."""
    result = await db.execute(
        select(Member).where(Member.id == member_id, Member.is_deleted == False)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Calculate attendance score (last 90 days)
    ninety_days_ago = date.today() - timedelta(days=90)
    att_count = (await db.execute(
        select(func.count()).where(
            AttendanceRecord.member_id == member_id,
            AttendanceRecord.date >= ninety_days_ago,
        )
    )).scalar() or 0
    attendance_score = min(att_count / 12.0, 1.0) * 100  # ~1 per week = 100

    # Calculate giving score (last 90 days)
    don_count = (await db.execute(
        select(func.count()).where(
            Donation.donor_id == member_id,
            Donation.date >= ninety_days_ago,
        )
    )).scalar() or 0
    giving_score = min(don_count / 12.0, 1.0) * 100

    # Group involvement score
    group_count = (await db.execute(
        select(func.count()).where(GroupMembership.member_id == member_id)
    )).scalar() or 0
    group_score = min(group_count / 2.0, 1.0) * 100

    # Serving score (placeholder—will be enhanced with volunteer module)
    serving_score = 0.0

    overall = (attendance_score * 0.35 + giving_score * 0.25 +
               group_score * 0.25 + serving_score * 0.15)

    if overall >= 80:
        level = "highly_engaged"
    elif overall >= 60:
        level = "engaged"
    elif overall >= 40:
        level = "somewhat_engaged"
    elif overall >= 20:
        level = "at_risk"
    else:
        level = "disengaged"

    return EngagementScore(
        member_id=member_id,
        member_name=f"{member.first_name} {member.last_name}",
        attendance_score=round(attendance_score, 1),
        giving_score=round(giving_score, 1),
        serving_score=round(serving_score, 1),
        group_score=round(group_score, 1),
        overall_score=round(overall, 1),
        level=level,
    )


@router.get("/search")
async def search_members_for_compose(
    q: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search members/users for compose-message flow."""
    from app.models.social import Follower
    from app.models.church import Church

    term = f"%{q}%"
    users = (await db.execute(
        select(User).where(
            or_(User.full_name.ilike(term), User.username.ilike(term))
        ).limit(20)
    )).scalars().all()

    items = []
    for u in users:
        church = None
        if u.church_id:
            church = (await db.execute(select(Church).where(Church.id == u.church_id))).scalar_one_or_none()

        fc = (await db.execute(
            select(func.count()).where(Follower.followed_id == u.id)
        )).scalar() or 0

        # Post count
        from app.models.feed import Post
        pc = (await db.execute(
            select(func.count()).where(Post.author_id == u.id, Post.is_deleted == False)
        )).scalar() or 0

        items.append({
            "id": u.id,
            "full_name": u.full_name,
            "username": u.username,
            "avatar_url": getattr(u, "avatar_url", None),
            "church_name": church.name if church else None,
            "followers_count": fc,
            "post_count": pc,
        })
    return {"data": items}

