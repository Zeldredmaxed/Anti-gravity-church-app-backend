"""Giving statements & chart data — PDF generation and chart-ready endpoints."""

import io
from datetime import date, datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from pydantic import BaseModel

from app.database import get_db
from app.models.donation import Donation
from app.models.member import Member
from app.models.fund import Fund
from app.models.user import User
from app.utils.security import get_current_user, require_permission

router = APIRouter(prefix="/giving", tags=["Giving & Statements"])


class ChartDataPoint(BaseModel):
    date: str
    amount: float


class GivingSummary(BaseModel):
    total: float
    count: int
    average: float


@router.get("/statements/{member_id}")
async def generate_giving_statement(
    member_id: int,
    year: int = Query(default=None, description="Tax year for the statement"),
    current_user: User = Depends(require_permission("finance:read")),
    db: AsyncSession = Depends(get_db),
):
    """Generate a PDF giving/tax statement for a member."""
    if year is None:
        year = date.today().year

    # Fetch member
    member = (await db.execute(select(Member).where(Member.id == member_id))).scalar_one_or_none()
    if not member:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Member not found")

    # Fetch donations for the year
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    result = await db.execute(
        select(Donation, Fund.name)
        .join(Fund, Donation.fund_id == Fund.id)
        .where(
            Donation.donor_id == member_id,
            Donation.date >= start_date,
            Donation.date <= end_date,
            Donation.status == "completed",
        )
        .order_by(Donation.date)
    )
    rows = result.all()

    # Generate PDF with fpdf2
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Header
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "Giving Statement", ln=True, align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Tax Year: {year}", ln=True, align="C")
    pdf.ln(5)

    # Member info
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"{member.first_name} {member.last_name}", ln=True)
    pdf.set_font("Helvetica", "", 10)
    if member.address:
        pdf.cell(0, 6, member.address, ln=True)
    if member.city:
        pdf.cell(0, 6, f"{member.city}, {member.state or ''} {member.zip_code or ''}", ln=True)
    pdf.ln(8)

    # Table header
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(35, 8, "Date", border=1, fill=True)
    pdf.cell(55, 8, "Fund", border=1, fill=True)
    pdf.cell(30, 8, "Type", border=1, fill=True)
    pdf.cell(25, 8, "Method", border=1, fill=True)
    pdf.cell(35, 8, "Amount", border=1, fill=True, align="R")
    pdf.ln()

    # Table rows
    pdf.set_font("Helvetica", "", 9)
    total = 0.0
    for donation, fund_name in rows:
        amt = float(donation.amount)
        total += amt
        pdf.cell(35, 7, str(donation.date), border=1)
        pdf.cell(55, 7, fund_name or "General", border=1)
        pdf.cell(30, 7, donation.donation_type or "", border=1)
        pdf.cell(25, 7, donation.payment_method or "", border=1)
        pdf.cell(35, 7, f"${amt:,.2f}", border=1, align="R")
        pdf.ln()

    # Total
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(145, 8, "Total:", border=1, align="R")
    pdf.cell(35, 8, f"${total:,.2f}", border=1, align="R")
    pdf.ln(12)

    # Disclaimer
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 5, (
        "This statement is provided for tax purposes. No goods or services were provided in exchange "
        "for these contributions. Please retain this statement for your tax records."
    ))

    # Return as streaming PDF
    pdf_bytes = pdf.output()
    buffer = io.BytesIO(pdf_bytes)
    filename = f"giving_statement_{member.last_name}_{year}.pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/chart-data", response_model=List[ChartDataPoint])
async def get_giving_chart_data(
    months: int = Query(12, ge=1, le=60, description="Number of months to look back"),
    current_user: User = Depends(require_permission("finance:read")),
    db: AsyncSession = Depends(get_db),
):
    """Get monthly giving totals formatted for chart rendering."""
    church_id = current_user.church_id
    cutoff = date.today() - timedelta(days=months * 30)

    result = await db.execute(
        select(
            func.to_char(Donation.date, 'YYYY-MM').label("month"),
            func.sum(Donation.amount).label("total"),
        )
        .where(
            Donation.church_id == church_id,
            Donation.date >= cutoff,
            Donation.status == "completed",
        )
        .group_by(func.to_char(Donation.date, 'YYYY-MM'))
        .order_by(func.to_char(Donation.date, 'YYYY-MM'))
    )

    return [ChartDataPoint(date=row.month, amount=float(row.total or 0)) for row in result.all()]


@router.get("/summary", response_model=GivingSummary)
async def get_giving_summary(
    period: str = Query("month", description="'month', 'quarter', or 'year'"),
    current_user: User = Depends(require_permission("finance:read")),
    db: AsyncSession = Depends(get_db),
):
    """Get giving summary for a time period."""
    church_id = current_user.church_id
    today = date.today()

    if period == "year":
        start = date(today.year, 1, 1)
    elif period == "quarter":
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        start = date(today.year, quarter_start_month, 1)
    else:
        start = today.replace(day=1)

    result = await db.execute(
        select(
            func.coalesce(func.sum(Donation.amount), 0).label("total"),
            func.count(Donation.id).label("count"),
        )
        .where(
            Donation.church_id == church_id,
            Donation.date >= start,
            Donation.status == "completed",
        )
    )
    row = result.one()
    total = float(row.total)
    count = int(row.count)

    return GivingSummary(
        total=total,
        count=count,
        average=total / count if count > 0 else 0,
    )
