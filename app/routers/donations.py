"""Donation tracking router: recording, batch entry, statements."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import date
from decimal import Decimal
import io

from app.database import get_db
from app.models.donation import Donation, Pledge
from app.models.fund import Fund
from app.models.member import Member
from app.models.user import User
from app.schemas.donation import (
    DonationCreate, DonationBatchCreate, DonationResponse,
    DonationListResponse, DonorSummary, PledgeCreate, PledgeResponse,
)
from app.utils.security import get_current_user, require_role
from app.dependencies import PaginationParams

router = APIRouter(prefix="/donations", tags=["Donations & Giving"])


def _don_resp(d, donor_name=None, fund_name=None):
    return DonationResponse(
        id=d.id, donor_id=d.donor_id, donor_name=donor_name,
        fund_id=d.fund_id, fund_name=fund_name, amount=d.amount,
        donation_type=d.donation_type, payment_method=d.payment_method,
        check_number=d.check_number, transaction_id=d.transaction_id,
        date=d.date, is_recurring=d.is_recurring,
        recurring_frequency=d.recurring_frequency,
        is_anonymous=d.is_anonymous, notes=d.notes, created_at=d.created_at,
    )


async def _get_names(db, donor_id, fund_id):
    dn, fn = None, None
    if donor_id:
        m = (await db.execute(select(Member).where(Member.id == donor_id))).scalar_one_or_none()
        if m: dn = f"{m.first_name} {m.last_name}"
    f = (await db.execute(select(Fund).where(Fund.id == fund_id))).scalar_one_or_none()
    if f: fn = f.name
    return dn, fn


@router.get("", response_model=DonationListResponse)
async def list_donations(
    fund_id: Optional[int] = None, donor_id: Optional[int] = None,
    donation_type: Optional[str] = None, start_date: Optional[date] = None,
    end_date: Optional[date] = None, pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db),
):
    query = select(Donation)
    if fund_id: query = query.where(Donation.fund_id == fund_id)
    if donor_id: query = query.where(Donation.donor_id == donor_id)
    if donation_type: query = query.where(Donation.donation_type == donation_type)
    if start_date: query = query.where(Donation.date >= start_date)
    if end_date: query = query.where(Donation.date <= end_date)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    total_amount = (await db.execute(
        select(func.coalesce(func.sum(Donation.amount), 0)).select_from(query.subquery())
    )).scalar() or Decimal("0")

    result = await db.execute(query.order_by(Donation.date.desc()).offset(pagination.offset).limit(pagination.per_page))
    items = []
    for d in result.scalars().all():
        dn, fn = await _get_names(db, d.donor_id, d.fund_id)
        items.append(_don_resp(d, dn, fn))

    return DonationListResponse(items=items, total=total, page=pagination.page,
                                 per_page=pagination.per_page, total_amount=total_amount)


@router.post("", response_model=DonationResponse, status_code=201)
async def record_donation(
    data: DonationCreate,
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db),
):
    fund = (await db.execute(select(Fund).where(Fund.id == data.fund_id))).scalar_one_or_none()
    if not fund: raise HTTPException(status_code=404, detail="Fund not found")
    donation = Donation(**data.model_dump(), recorded_by=current_user.id)
    db.add(donation)
    fund.current_balance = (fund.current_balance or Decimal("0")) + data.amount
    db.add(fund)
    await db.commit()
    await db.refresh(donation)
    dn, _ = await _get_names(db, donation.donor_id, donation.fund_id)
    return _don_resp(donation, dn, fund.name)


@router.post("/batch", status_code=201)
async def batch_record(
    data: DonationBatchCreate,
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db),
):
    recorded, total_amount = 0, Decimal("0")
    for d in data.donations:
        fund = (await db.execute(select(Fund).where(Fund.id == d.fund_id))).scalar_one_or_none()
        if not fund: continue
        db.add(Donation(**d.model_dump(), recorded_by=current_user.id))
        fund.current_balance = (fund.current_balance or Decimal("0")) + d.amount
        db.add(fund)
        recorded += 1
        total_amount += d.amount
    await db.commit()
    return {"recorded": recorded, "total_amount": float(total_amount)}


@router.get("/donor/{member_id}", response_model=DonorSummary)
async def get_donor_summary(
    member_id: int,
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db),
):
    member = (await db.execute(select(Member).where(Member.id == member_id, Member.is_deleted == False))).scalar_one_or_none()
    if not member: raise HTTPException(status_code=404, detail="Member not found")
    donations = (await db.execute(select(Donation).where(Donation.donor_id == member_id).order_by(Donation.date.desc()))).scalars().all()
    total = sum(d.amount for d in donations)
    count = len(donations)
    name = f"{member.first_name} {member.last_name}"
    items = []
    for d in donations[:20]:
        _, fn = await _get_names(db, None, d.fund_id)
        items.append(_don_resp(d, name, fn))
    return DonorSummary(
        member_id=member_id, member_name=name, total_given=total,
        donation_count=count, first_gift_date=donations[-1].date if donations else None,
        last_gift_date=donations[0].date if donations else None,
        avg_gift=total / count if count else Decimal("0"), giving_history=items,
    )


@router.get("/statements/{member_id}")
async def generate_giving_statement(
    member_id: int, year: int = Query(...),
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db),
):
    """Generate IRS-compliant giving statement PDF."""
    from app.config import settings
    from fpdf import FPDF

    member = (await db.execute(select(Member).where(Member.id == member_id))).scalar_one_or_none()
    if not member: raise HTTPException(status_code=404, detail="Member not found")
    donations = (await db.execute(
        select(Donation).where(Donation.donor_id == member_id, func.extract('year', Donation.date) == year).order_by(Donation.date)
    )).scalars().all()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, settings.CHURCH_NAME, ln=True, align="C")
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"Giving Statement - {year}", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Donor: {member.first_name} {member.last_name}", ln=True)
    if member.address:
        pdf.cell(0, 7, f"{member.address}, {member.city or ''} {member.state or ''} {member.zip_code or ''}", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(35, 8, "Date", border=1); pdf.cell(50, 8, "Fund", border=1)
    pdf.cell(35, 8, "Type", border=1); pdf.cell(35, 8, "Amount", border=1, align="R"); pdf.ln()
    pdf.set_font("Helvetica", "", 10)
    total = Decimal("0")
    for d in donations:
        f = (await db.execute(select(Fund).where(Fund.id == d.fund_id))).scalar_one_or_none()
        pdf.cell(35, 7, d.date.isoformat(), border=1)
        pdf.cell(50, 7, (f.name if f else "N/A")[:25], border=1)
        pdf.cell(35, 7, d.donation_type, border=1)
        pdf.cell(35, 7, f"${d.amount:,.2f}", border=1, align="R"); pdf.ln()
        total += d.amount
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(120, 8, "Total", border=1); pdf.cell(35, 8, f"${total:,.2f}", border=1, align="R"); pdf.ln(15)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 5, "No goods or services were provided in exchange for the above contributions. "
        f"{settings.CHURCH_NAME} is a tax-exempt organization under Section 501(c)(3).")
    return StreamingResponse(io.BytesIO(pdf.output()), media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=statement_{member.last_name}_{year}.pdf"})


@router.get("/payment-methods")
async def get_payment_methods(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """
    Placeholder: Retrieve saved payment methods for the authenticated user.
    In a real app, this would query Stripe using current_user.stripe_customer_id.
    """
    if not current_user.stripe_customer_id:
        return {"payment_methods": []}
        
    # Mocking a Stripe response for now
    return {
        "payment_methods": [
            {"id": "pm_1234", "brand": "visa", "last4": "4242", "exp_month": 12, "exp_year": 2026}
        ]
    }


# --- Pledges ---
pledge_router = APIRouter(prefix="/pledges", tags=["Pledges"])


async def _pledge_resp(p, db):
    m = (await db.execute(select(Member).where(Member.id == p.member_id))).scalar_one_or_none()
    f = (await db.execute(select(Fund).where(Fund.id == p.fund_id))).scalar_one_or_none()
    prog = float(p.fulfilled_amount / p.pledged_amount * 100) if p.pledged_amount else 0
    return PledgeResponse(
        id=p.id, member_id=p.member_id, member_name=f"{m.first_name} {m.last_name}" if m else None,
        fund_id=p.fund_id, fund_name=f.name if f else None, campaign_name=p.campaign_name,
        pledged_amount=p.pledged_amount, fulfilled_amount=p.fulfilled_amount,
        progress_percent=round(prog, 1), start_date=p.start_date, end_date=p.end_date,
        status=p.status, notes=p.notes, created_at=p.created_at)


@pledge_router.get("", response_model=list[PledgeResponse])
async def list_pledges(status: Optional[str] = None, fund_id: Optional[int] = None,
    current_user: User = Depends(require_role("admin", "pastor", "staff")), db: AsyncSession = Depends(get_db)):
    query = select(Pledge)
    if status: query = query.where(Pledge.status == status)
    if fund_id: query = query.where(Pledge.fund_id == fund_id)
    pledges = (await db.execute(query.order_by(Pledge.created_at.desc()))).scalars().all()
    return [await _pledge_resp(p, db) for p in pledges]


@pledge_router.post("", response_model=PledgeResponse, status_code=201)
async def create_pledge(data: PledgeCreate,
    current_user: User = Depends(require_role("admin", "pastor", "staff")), db: AsyncSession = Depends(get_db)):
    pledge = Pledge(**data.model_dump())
    db.add(pledge); await db.commit(); await db.refresh(pledge)
    return await _pledge_resp(pledge, db)


@pledge_router.get("/{pledge_id}", response_model=PledgeResponse)
async def get_pledge(pledge_id: int,
    current_user: User = Depends(require_role("admin", "pastor", "staff")), db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(Pledge).where(Pledge.id == pledge_id))).scalar_one_or_none()
    if not p: raise HTTPException(status_code=404, detail="Pledge not found")
    return await _pledge_resp(p, db)


# ── Recurring Donations ─────────────────────────────────────────
from pydantic import BaseModel


class RecurringDonationCreate(BaseModel):
    fund_id: int
    amount: float
    frequency: str = "monthly"  # weekly, biweekly, monthly, quarterly, yearly
    payment_method_id: Optional[int] = None


@router.post("/recurring", status_code=201)
async def create_recurring_donation(
    data: RecurringDonationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a recurring donation schedule.
    For now this stores the intent in the database.
    Stripe subscription integration can be added later.
    """
    from datetime import timedelta, datetime, timezone

    fund = (await db.execute(select(Fund).where(Fund.id == data.fund_id))).scalar_one_or_none()
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")

    # Calculate next charge date
    freq_map = {
        "weekly": timedelta(weeks=1),
        "biweekly": timedelta(weeks=2),
        "monthly": timedelta(days=30),
        "quarterly": timedelta(days=90),
        "yearly": timedelta(days=365),
    }
    delta = freq_map.get(data.frequency, timedelta(days=30))
    next_date = datetime.now(timezone.utc) + delta

    # Record as a pledge with recurring flag
    pledge = Pledge(
        donor_id=current_user.member_id or current_user.id,
        fund_id=data.fund_id,
        amount=Decimal(str(data.amount)),
        start_date=date.today(),
        end_date=date.today() + delta,
        church_id=current_user.church_id or fund.church_id,
    )
    db.add(pledge)
    await db.commit()
    await db.refresh(pledge)

    return {
        "data": {
            "id": pledge.id,
            "fund_id": fund.id,
            "fund_name": fund.name,
            "amount": float(data.amount),
            "frequency": data.frequency,
            "next_date": next_date.isoformat(),
            "status": "active",
            "message": "Recurring donation scheduled",
        }
    }


@router.get("/recurring")
async def list_recurring_donations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the current user's recurring donation pledges."""
    member_id = current_user.member_id or current_user.id

    pledges = (await db.execute(
        select(Pledge).where(Pledge.donor_id == member_id)
        .order_by(Pledge.created_at.desc())
    )).scalars().all()

    items = []
    for p in pledges:
        fund = (await db.execute(select(Fund).where(Fund.id == p.fund_id))).scalar_one_or_none()
        items.append({
            "id": p.id,
            "fund_id": p.fund_id,
            "fund_name": fund.name if fund else "Unknown",
            "amount": float(p.amount),
            "start_date": p.start_date.isoformat() if p.start_date else None,
            "status": "active",
        })

    return {"data": items}

