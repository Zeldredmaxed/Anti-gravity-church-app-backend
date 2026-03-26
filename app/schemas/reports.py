"""Pydantic schemas for reporting and dashboard."""

from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from decimal import Decimal


class DashboardSummary(BaseModel):
    # Membership
    total_members: int
    active_members: int
    new_members_this_month: int
    new_visitors_this_month: int

    # Attendance
    avg_weekly_attendance: float
    last_sunday_attendance: int
    attendance_trend_percent: float  # +/- vs prior period

    # Giving
    total_giving_this_month: Decimal
    total_giving_ytd: Decimal
    giving_trend_percent: float  # +/- vs same month last year
    unique_donors_this_month: int

    # Groups
    active_groups: int
    total_group_members: int


class GivingAnalytics(BaseModel):
    total_amount: Decimal
    donation_count: int
    unique_donors: int
    avg_donation: Decimal
    by_fund: List["FundGivingSummary"]
    by_type: List["TypeGivingSummary"]
    by_method: List["MethodGivingSummary"]
    lapsed_donors: int  # donors who gave last period but not this period
    first_time_donors: int
    recurring_donors: int


class FundGivingSummary(BaseModel):
    fund_id: int
    fund_name: str
    total: Decimal
    count: int


class TypeGivingSummary(BaseModel):
    donation_type: str
    total: Decimal
    count: int


class MethodGivingSummary(BaseModel):
    payment_method: str
    total: Decimal
    count: int


class AttendanceAnalytics(BaseModel):
    total_records: int
    avg_attendance: float
    peak_attendance: int
    peak_date: Optional[date] = None
    by_service: List["ServiceAttendanceSummary"]
    first_time_guests_total: int


class ServiceAttendanceSummary(BaseModel):
    service_id: int
    service_name: str
    avg_attendance: float
    total_records: int


class EngagementDistribution(BaseModel):
    highly_engaged: int
    engaged: int
    somewhat_engaged: int
    at_risk: int
    disengaged: int
    total_scored: int


class FinancialSummary(BaseModel):
    fund_id: int
    fund_name: str
    fund_type: str
    total_income: Decimal
    total_expenses: Decimal
    net: Decimal
    budgeted: Optional[Decimal] = None
    budget_variance: Optional[Decimal] = None
    is_restricted: bool
