"""Fund accounting router: CRUD, budgets, expenses."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from decimal import Decimal

from app.database import get_db
from app.models.fund import Fund, Budget, Expense
from app.models.donation import Donation
from app.models.user import User
from app.schemas.fund import (
    FundCreate, FundUpdate, FundResponse, FundDetailResponse,
    BudgetCreate, BudgetResponse, ExpenseCreate, ExpenseResponse,
)
from app.utils.security import get_current_user, require_role

router = APIRouter(prefix="/funds", tags=["Fund Accounting"])


@router.get("", response_model=list[FundResponse])
async def list_funds(
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all funds with balances."""
    query = select(Fund)
    if is_active is not None:
        query = query.where(Fund.is_active == is_active)
    query = query.order_by(Fund.name)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=FundResponse, status_code=201)
async def create_fund(
    data: FundCreate,
    current_user: User = Depends(require_role("admin", "pastor")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new fund."""
    # Check for duplicate name
    existing = await db.execute(select(Fund).where(Fund.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Fund name already exists")

    fund = Fund(**data.model_dump())
    db.add(fund)
    await db.flush()
    await db.refresh(fund)
    return fund


@router.get("/{fund_id}", response_model=FundDetailResponse)
async def get_fund(
    fund_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get fund details with budget and income/expense summary."""
    result = await db.execute(select(Fund).where(Fund.id == fund_id))
    fund = result.scalar_one_or_none()
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")

    # Total income (donations)
    total_income = (await db.execute(
        select(func.coalesce(func.sum(Donation.amount), 0)).where(Donation.fund_id == fund_id)
    )).scalar() or Decimal("0")

    # Total expenses
    total_expenses = (await db.execute(
        select(func.coalesce(func.sum(Expense.amount), 0)).where(Expense.fund_id == fund_id)
    )).scalar() or Decimal("0")

    # Budgets
    budget_result = await db.execute(
        select(Budget).where(Budget.fund_id == fund_id).order_by(Budget.fiscal_year.desc())
    )
    budgets = budget_result.scalars().all()

    return FundDetailResponse(
        id=fund.id,
        name=fund.name,
        description=fund.description,
        fund_type=fund.fund_type,
        is_restricted=fund.is_restricted,
        is_active=fund.is_active,
        target_amount=fund.target_amount,
        current_balance=fund.current_balance,
        created_at=fund.created_at,
        total_income=total_income,
        total_expenses=total_expenses,
        budgets=[BudgetResponse.model_validate(b) for b in budgets],
    )


@router.put("/{fund_id}", response_model=FundResponse)
async def update_fund(
    fund_id: int,
    data: FundUpdate,
    current_user: User = Depends(require_role("admin", "pastor")),
    db: AsyncSession = Depends(get_db),
):
    """Update a fund."""
    result = await db.execute(select(Fund).where(Fund.id == fund_id))
    fund = result.scalar_one_or_none()
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(fund, field, value)

    db.add(fund)
    await db.flush()
    await db.refresh(fund)
    return fund


@router.post("/{fund_id}/budgets", response_model=BudgetResponse, status_code=201)
async def set_budget(
    fund_id: int,
    data: BudgetCreate,
    current_user: User = Depends(require_role("admin", "pastor")),
    db: AsyncSession = Depends(get_db),
):
    """Set or update a budget for a fund."""
    # Verify fund exists
    fund_result = await db.execute(select(Fund).where(Fund.id == fund_id))
    if not fund_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Fund not found")

    budget = Budget(fund_id=fund_id, **data.model_dump())
    db.add(budget)
    await db.flush()
    await db.refresh(budget)
    return budget


@router.post("/{fund_id}/expenses", response_model=ExpenseResponse, status_code=201)
async def record_expense(
    fund_id: int,
    data: ExpenseCreate,
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db),
):
    """Record an expense against a fund."""
    fund_result = await db.execute(select(Fund).where(Fund.id == fund_id))
    fund = fund_result.scalar_one_or_none()
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")

    # Check restricted fund controls
    if fund.is_restricted:
        balance = fund.current_balance or Decimal("0")
        if data.amount > balance:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient funds in restricted fund '{fund.name}'. "
                       f"Balance: {balance}, Requested: {data.amount}",
            )

    expense = Expense(
        fund_id=fund_id,
        approved_by=current_user.id,
        **data.model_dump(),
    )
    db.add(expense)

    # Update fund balance
    fund.current_balance = (fund.current_balance or Decimal("0")) - data.amount
    db.add(fund)

    await db.flush()
    await db.refresh(expense)
    return expense


@router.get("/{fund_id}/transactions", response_model=dict)
async def get_fund_transactions(
    fund_id: int,
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db),
):
    """Get income and expense timeline for a fund."""
    # Verify fund exists
    fund_result = await db.execute(select(Fund).where(Fund.id == fund_id))
    fund = fund_result.scalar_one_or_none()
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")

    # Recent donations
    don_result = await db.execute(
        select(Donation).where(Donation.fund_id == fund_id)
        .order_by(Donation.date.desc()).limit(50)
    )
    donations = don_result.scalars().all()

    # Recent expenses
    exp_result = await db.execute(
        select(Expense).where(Expense.fund_id == fund_id)
        .order_by(Expense.date.desc()).limit(50)
    )
    expenses = exp_result.scalars().all()

    return {
        "fund_name": fund.name,
        "current_balance": float(fund.current_balance or 0),
        "income": [
            {
                "id": d.id, "amount": float(d.amount), "date": d.date.isoformat(),
                "type": d.donation_type, "method": d.payment_method,
            }
            for d in donations
        ],
        "expenses": [
            {
                "id": e.id, "amount": float(e.amount), "date": e.date.isoformat(),
                "description": e.description, "vendor": e.vendor, "category": e.category,
            }
            for e in expenses
        ],
    }
