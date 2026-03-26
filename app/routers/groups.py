"""Groups management router."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import date

from app.database import get_db
from app.models.group import Group, GroupMembership
from app.models.member import Member
from app.models.user import User
from app.schemas.group import (
    GroupCreate, GroupUpdate, GroupMemberAdd,
    GroupResponse, GroupDetailResponse, GroupMemberResponse,
)
from app.utils.security import get_current_user, require_role

router = APIRouter(prefix="/groups", tags=["Groups & Small Groups"])


@router.get("", response_model=list[GroupResponse])
async def list_groups(
    group_type: Optional[str] = None, is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = select(Group)
    if group_type: query = query.where(Group.group_type == group_type)
    if is_active is not None: query = query.where(Group.is_active == is_active)
    groups = (await db.execute(query.order_by(Group.name))).scalars().all()
    items = []
    for g in groups:
        count = (await db.execute(select(func.count()).where(GroupMembership.group_id == g.id))).scalar() or 0
        leader_name = None
        if g.leader_id:
            ldr = (await db.execute(select(Member).where(Member.id == g.leader_id))).scalar_one_or_none()
            if ldr: leader_name = f"{ldr.first_name} {ldr.last_name}"
        items.append(GroupResponse(
            id=g.id, name=g.name, description=g.description, group_type=g.group_type,
            leader_id=g.leader_id, leader_name=leader_name, meeting_day=g.meeting_day,
            meeting_time=g.meeting_time, meeting_location=g.meeting_location,
            is_active=g.is_active, max_capacity=g.max_capacity, member_count=count,
            campus=g.campus, created_at=g.created_at))
    return items


@router.post("", response_model=GroupResponse, status_code=201)
async def create_group(data: GroupCreate,
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db)):
    group = Group(**data.model_dump()); db.add(group); await db.flush(); await db.refresh(group)
    return GroupResponse(
        id=group.id, name=group.name, description=group.description,
        group_type=group.group_type, leader_id=group.leader_id, leader_name=None,
        meeting_day=group.meeting_day, meeting_time=group.meeting_time,
        meeting_location=group.meeting_location, is_active=group.is_active,
        max_capacity=group.max_capacity, member_count=0, campus=group.campus,
        created_at=group.created_at)


@router.get("/{group_id}", response_model=GroupDetailResponse)
async def get_group(group_id: int, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    g = (await db.execute(select(Group).where(Group.id == group_id))).scalar_one_or_none()
    if not g: raise HTTPException(status_code=404, detail="Group not found")
    memberships = (await db.execute(select(GroupMembership).where(
        GroupMembership.group_id == group_id))).scalars().all()
    members = []
    for gm in memberships:
        m = (await db.execute(select(Member).where(Member.id == gm.member_id))).scalar_one_or_none()
        members.append(GroupMemberResponse(
            id=gm.id, member_id=gm.member_id,
            member_name=f"{m.first_name} {m.last_name}" if m else None,
            role=gm.role, joined_date=gm.joined_date))
    leader_name = None
    if g.leader_id:
        ldr = (await db.execute(select(Member).where(Member.id == g.leader_id))).scalar_one_or_none()
        if ldr: leader_name = f"{ldr.first_name} {ldr.last_name}"
    return GroupDetailResponse(
        id=g.id, name=g.name, description=g.description, group_type=g.group_type,
        leader_id=g.leader_id, leader_name=leader_name, meeting_day=g.meeting_day,
        meeting_time=g.meeting_time, meeting_location=g.meeting_location,
        is_active=g.is_active, max_capacity=g.max_capacity,
        member_count=len(memberships), campus=g.campus,
        created_at=g.created_at, members=members)


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(group_id: int, data: GroupUpdate,
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db)):
    g = (await db.execute(select(Group).where(Group.id == group_id))).scalar_one_or_none()
    if not g: raise HTTPException(status_code=404, detail="Group not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(g, field, value)
    db.add(g); await db.flush(); await db.refresh(g)
    count = (await db.execute(select(func.count()).where(GroupMembership.group_id == g.id))).scalar() or 0
    return GroupResponse(
        id=g.id, name=g.name, description=g.description, group_type=g.group_type,
        leader_id=g.leader_id, leader_name=None, meeting_day=g.meeting_day,
        meeting_time=g.meeting_time, meeting_location=g.meeting_location,
        is_active=g.is_active, max_capacity=g.max_capacity, member_count=count,
        campus=g.campus, created_at=g.created_at)


@router.post("/{group_id}/members", status_code=201)
async def add_group_member(group_id: int, data: GroupMemberAdd,
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db)):
    g = (await db.execute(select(Group).where(Group.id == group_id))).scalar_one_or_none()
    if not g: raise HTTPException(status_code=404, detail="Group not found")
    # Check capacity
    if g.max_capacity:
        count = (await db.execute(select(func.count()).where(GroupMembership.group_id == group_id))).scalar() or 0
        if count >= g.max_capacity:
            raise HTTPException(status_code=400, detail="Group at maximum capacity")
    existing = (await db.execute(select(GroupMembership).where(
        GroupMembership.group_id == group_id, GroupMembership.member_id == data.member_id
    ))).scalar_one_or_none()
    if existing: raise HTTPException(status_code=400, detail="Member already in group")
    gm = GroupMembership(group_id=group_id, member_id=data.member_id,
                          role=data.role, joined_date=date.today())
    db.add(gm); await db.flush()
    return {"message": "Member added to group", "membership_id": gm.id}


@router.delete("/{group_id}/members/{member_id}", status_code=204)
async def remove_group_member(group_id: int, member_id: int,
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db)):
    gm = (await db.execute(select(GroupMembership).where(
        GroupMembership.group_id == group_id, GroupMembership.member_id == member_id
    ))).scalar_one_or_none()
    if not gm: raise HTTPException(status_code=404, detail="Membership not found")
    await db.delete(gm)
