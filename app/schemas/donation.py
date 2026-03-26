"""Pydantic schemas for donations and pledges."""

from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


class DonationCreate(BaseModel):
    donor_id: Optional[int] = None
    fund_id: int
    amount: Decimal
    donation_type: str = "offering"
    payment_method: str = "cash"
    check_number: Optional[str] = None
    transaction_id: Optional[str] = None
    date: date
    is_recurring: bool = False
    recurring_frequency: Optional[str] = None
    is_anonymous: bool = False
    notes: Optional[str] = None


class DonationBatchCreate(BaseModel):
    donations: List[DonationCreate]


class DonationResponse(BaseModel):
    id: int
    donor_id: Optional[int] = None
    donor_name: Optional[str] = None
    fund_id: int
    fund_name: Optional[str] = None
    amount: Decimal
    donation_type: str
    payment_method: str
    check_number: Optional[str] = None
    transaction_id: Optional[str] = None
    date: date
    is_recurring: bool
    recurring_frequency: Optional[str] = None
    is_anonymous: bool
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DonationListResponse(BaseModel):
    items: List[DonationResponse]
    total: int
    page: int
    per_page: int
    total_amount: Decimal


class DonorSummary(BaseModel):
    member_id: int
    member_name: str
    total_given: Decimal
    donation_count: int
    first_gift_date: Optional[date] = None
    last_gift_date: Optional[date] = None
    avg_gift: Decimal
    giving_history: List[DonationResponse] = []


class PledgeCreate(BaseModel):
    member_id: int
    fund_id: int
    campaign_name: Optional[str] = None
    pledged_amount: Decimal
    start_date: date
    end_date: Optional[date] = None
    notes: Optional[str] = None


class PledgeResponse(BaseModel):
    id: int
    member_id: int
    member_name: Optional[str] = None
    fund_id: int
    fund_name: Optional[str] = None
    campaign_name: Optional[str] = None
    pledged_amount: Decimal
    fulfilled_amount: Decimal
    progress_percent: float = 0.0
    start_date: date
    end_date: Optional[date] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
