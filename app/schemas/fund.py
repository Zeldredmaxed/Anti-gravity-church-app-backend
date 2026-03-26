"""Pydantic schemas for fund accounting."""

from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


class FundCreate(BaseModel):
    name: str
    description: Optional[str] = None
    fund_type: str = "general"
    is_restricted: bool = False
    target_amount: Optional[Decimal] = None


class FundUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    fund_type: Optional[str] = None
    is_restricted: Optional[bool] = None
    is_active: Optional[bool] = None
    target_amount: Optional[Decimal] = None


class FundResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    fund_type: str
    is_restricted: bool
    is_active: bool
    target_amount: Optional[Decimal] = None
    current_balance: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


class FundDetailResponse(FundResponse):
    total_income: Decimal = Decimal("0")
    total_expenses: Decimal = Decimal("0")
    budgets: List["BudgetResponse"] = []


class BudgetCreate(BaseModel):
    fiscal_year: int
    budgeted_amount: Decimal
    period: str = "annual"
    notes: Optional[str] = None


class BudgetResponse(BaseModel):
    id: int
    fund_id: int
    fiscal_year: int
    budgeted_amount: Decimal
    period: str
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ExpenseCreate(BaseModel):
    amount: Decimal
    description: str
    vendor: Optional[str] = None
    category: Optional[str] = None
    date: date
    check_number: Optional[str] = None
    receipt_url: Optional[str] = None
    notes: Optional[str] = None


class ExpenseResponse(BaseModel):
    id: int
    fund_id: int
    amount: Decimal
    description: str
    vendor: Optional[str] = None
    category: Optional[str] = None
    date: date
    check_number: Optional[str] = None
    receipt_url: Optional[str] = None
    approved_by: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
