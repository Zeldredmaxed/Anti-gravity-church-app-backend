from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
from app.database import get_db
from app.models.automation import AutomationRule
from app.models.user import User
from app.schemas.automation import (
    AutomationRuleCreate, AutomationRuleUpdate, AutomationRuleResponse, AutomationRuleListResponse
)
from app.utils.security import get_current_user, require_role, get_church_id
from app.dependencies import PaginationParams

router = APIRouter(prefix="/automations", tags=["Automations"])


@router.get("", response_model=AutomationRuleListResponse)
async def list_automations(
    is_active: Optional[bool] = Query(None),
    trigger_type: Optional[str] = Query(None),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db),
):
    """List automation rules."""
    query = select(AutomationRule).where(AutomationRule.church_id == current_user.church_id)

    if is_active is not None:
        query = query.where(AutomationRule.is_active == is_active)
    if trigger_type:
        query = query.where(AutomationRule.trigger_type == trigger_type)

    total_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(total_query)

    query = query.offset(pagination.skip).limit(pagination.limit).order_by(AutomationRule.created_at.desc())
    result = await db.execute(query)
    rules = result.scalars().all()

    return {
        "data": rules,
        "total": total,
        "page": pagination.page,
        "size": pagination.size
    }


@router.post("", response_model=AutomationRuleResponse)
async def create_automation(
    rule_in: AutomationRuleCreate,
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new automation rule."""
    rule = AutomationRule(**rule_in.model_dump(), church_id=current_user.church_id)
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.get("/{rule_id}", response_model=AutomationRuleResponse)
async def get_automation(
    rule_id: int,
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db),
):
    """Get specific automation rule."""
    result = await db.execute(
        select(AutomationRule).where(
            AutomationRule.id == rule_id,
            AutomationRule.church_id == current_user.church_id
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Automation rule not found")
    return rule


@router.put("/{rule_id}", response_model=AutomationRuleResponse)
async def update_automation(
    rule_id: int,
    rule_in: AutomationRuleUpdate,
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db),
):
    """Update an automation rule."""
    result = await db.execute(
        select(AutomationRule).where(
            AutomationRule.id == rule_id,
            AutomationRule.church_id == current_user.church_id
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Automation rule not found")

    update_data = rule_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)

    await db.commit()
    await db.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=204)
async def delete_automation(
    rule_id: int,
    current_user: User = Depends(require_role("admin", "pastor")),
    db: AsyncSession = Depends(get_db),
):
    """Delete an automation rule."""
    result = await db.execute(
        select(AutomationRule).where(
            AutomationRule.id == rule_id,
            AutomationRule.church_id == current_user.church_id
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Automation rule not found")

    await db.delete(rule)
    await db.commit()
