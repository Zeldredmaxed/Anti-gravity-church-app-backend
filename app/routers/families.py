"""Family management router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.family import Family, FamilyRelationship
from app.models.member import Member
from app.models.user import User
from app.schemas.family import (
    FamilyCreate, FamilyUpdate, FamilyMemberAdd,
    FamilyResponse, FamilyDetailResponse, FamilyRelationshipResponse,
)
from app.utils.security import get_current_user, require_role

router = APIRouter(prefix="/families", tags=["Families"])


@router.get("", response_model=list[FamilyResponse])
async def list_families(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all families with member counts."""
    result = await db.execute(select(Family).order_by(Family.family_name))
    families = result.scalars().all()

    response = []
    for f in families:
        member_count = (await db.execute(
            select(func.count()).where(Member.family_id == f.id, Member.is_deleted == False)
        )).scalar() or 0

        resp = FamilyResponse(
            id=f.id,
            family_name=f.family_name,
            address=f.address,
            city=f.city,
            state=f.state,
            zip_code=f.zip_code,
            phone=f.phone,
            member_count=member_count,
            created_at=f.created_at,
        )
        response.append(resp)
    return response


@router.post("", response_model=FamilyResponse, status_code=201)
async def create_family(
    data: FamilyCreate,
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new family/household."""
    family = Family(**data.model_dump())
    db.add(family)
    await db.commit()
    await db.refresh(family)
    return FamilyResponse(
        id=family.id,
        family_name=family.family_name,
        address=family.address,
        city=family.city,
        state=family.state,
        zip_code=family.zip_code,
        phone=family.phone,
        member_count=0,
        created_at=family.created_at,
    )


@router.get("/{family_id}", response_model=FamilyDetailResponse)
async def get_family(
    family_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get family details with all members and relationships."""
    result = await db.execute(select(Family).where(Family.id == family_id))
    family = result.scalar_one_or_none()
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")

    # Get relationships with member names
    rel_result = await db.execute(
        select(FamilyRelationship).where(FamilyRelationship.family_id == family_id)
    )
    relationships = rel_result.scalars().all()

    rel_responses = []
    for r in relationships:
        member_result = await db.execute(select(Member).where(Member.id == r.member_id))
        member = member_result.scalar_one_or_none()
        member_name = f"{member.first_name} {member.last_name}" if member else None

        rel_responses.append(FamilyRelationshipResponse(
            id=r.id,
            member_id=r.member_id,
            relationship_type=r.relationship_type,
            member_name=member_name,
        ))

    member_count = (await db.execute(
        select(func.count()).where(Member.family_id == family_id, Member.is_deleted == False)
    )).scalar() or 0

    return FamilyDetailResponse(
        id=family.id,
        family_name=family.family_name,
        address=family.address,
        city=family.city,
        state=family.state,
        zip_code=family.zip_code,
        phone=family.phone,
        member_count=member_count,
        created_at=family.created_at,
        relationships=rel_responses,
    )


@router.put("/{family_id}", response_model=FamilyResponse)
async def update_family(
    family_id: int,
    data: FamilyUpdate,
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db),
):
    """Update a family."""
    result = await db.execute(select(Family).where(Family.id == family_id))
    family = result.scalar_one_or_none()
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(family, field, value)

    db.add(family)
    await db.commit()
    await db.refresh(family)

    member_count = (await db.execute(
        select(func.count()).where(Member.family_id == family_id, Member.is_deleted == False)
    )).scalar() or 0

    return FamilyResponse(
        id=family.id,
        family_name=family.family_name,
        address=family.address,
        city=family.city,
        state=family.state,
        zip_code=family.zip_code,
        phone=family.phone,
        member_count=member_count,
        created_at=family.created_at,
    )


@router.post("/{family_id}/members", status_code=201)
async def add_member_to_family(
    family_id: int,
    data: FamilyMemberAdd,
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db),
):
    """Add a member to a family with a relationship type."""
    # Verify family exists
    fam_result = await db.execute(select(Family).where(Family.id == family_id))
    if not fam_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Family not found")

    # Verify member exists
    mem_result = await db.execute(
        select(Member).where(Member.id == data.member_id, Member.is_deleted == False)
    )
    member = mem_result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Update member's family_id
    member.family_id = family_id
    db.add(member)

    # Create relationship record
    rel = FamilyRelationship(
        family_id=family_id,
        member_id=data.member_id,
        relationship_type=data.relationship_type,
    )
    db.add(rel)
    await db.commit()

    return {"message": "Member added to family", "relationship_id": rel.id}


@router.delete("/{family_id}/members/{member_id}", status_code=204)
async def remove_member_from_family(
    family_id: int,
    member_id: int,
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db),
):
    """Remove a member from a family."""
    # Remove relationship
    rel_result = await db.execute(
        select(FamilyRelationship).where(
            FamilyRelationship.family_id == family_id,
            FamilyRelationship.member_id == member_id,
        )
    )
    rel = rel_result.scalar_one_or_none()
    if rel:
        await db.delete(rel)

    # Clear member's family_id
    mem_result = await db.execute(select(Member).where(Member.id == member_id))
    member = mem_result.scalar_one_or_none()
    if member and member.family_id == family_id:
        member.family_id = None
        db.add(member)
