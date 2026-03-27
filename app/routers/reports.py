"""Reports & dashboard router."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import date, timedelta
from decimal import Decimal
import csv, io

from app.database import get_db
from app.models.member import Member
from app.models.donation import Donation
from app.models.fund import Fund, Budget, Expense
from app.models.attendance import AttendanceRecord, Service
from app.models.group import Group, GroupMembership
from app.models.user import User
from app.schemas.reports import (
    DashboardSummary, GivingAnalytics, FundGivingSummary,
    TypeGivingSummary, MethodGivingSummary, AttendanceAnalytics,
    ServiceAttendanceSummary, EngagementDistribution, FinancialSummary,
)
from app.utils.security import get_current_user, require_role

router = APIRouter(prefix="/reports", tags=["Reports & Analytics"])


@router.get("/dashboard", response_model=DashboardSummary)
async def dashboard(db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pastor", "staff"))):
    today = date.today()
    month_start = today.replace(day=1)
    last_sunday = today - timedelta(days=(today.weekday() + 1) % 7)

    total_members = (await db.execute(select(func.count()).where(Member.is_deleted == False))).scalar() or 0
    active_members = (await db.execute(select(func.count()).where(
        Member.is_deleted == False, Member.membership_status.in_(["active", "member"])))).scalar() or 0
    new_members = (await db.execute(select(func.count()).where(
        Member.is_deleted == False, Member.join_date >= month_start))).scalar() or 0
    new_visitors = (await db.execute(select(func.count()).where(
        Member.is_deleted == False, Member.membership_status == "visitor",
        Member.created_at >= month_start))).scalar() or 0

    # Attendance
    four_weeks_ago = today - timedelta(weeks=4)
    four_week_att = (await db.execute(select(func.count()).where(
        AttendanceRecord.date >= four_weeks_ago))).scalar() or 0
    avg_weekly = four_week_att / 4.0
    last_sun = (await db.execute(select(func.count()).where(
        AttendanceRecord.date == last_sunday))).scalar() or 0
    eight_weeks_ago = today - timedelta(weeks=8)
    prior_att = (await db.execute(select(func.count()).where(
        AttendanceRecord.date >= eight_weeks_ago, AttendanceRecord.date < four_weeks_ago))).scalar() or 1
    att_trend = ((four_week_att - prior_att) / max(prior_att, 1)) * 100

    # Giving
    month_giving = (await db.execute(select(func.coalesce(func.sum(Donation.amount), 0)).where(
        Donation.date >= month_start))).scalar() or Decimal("0")
    year_start = today.replace(month=1, day=1)
    ytd_giving = (await db.execute(select(func.coalesce(func.sum(Donation.amount), 0)).where(
        Donation.date >= year_start))).scalar() or Decimal("0")
    last_year_month = month_start.replace(year=month_start.year - 1)
    last_year_end = (last_year_month.replace(month=last_year_month.month % 12 + 1, day=1) - timedelta(days=1)) if last_year_month.month < 12 else date(last_year_month.year, 12, 31)
    ly_giving = (await db.execute(select(func.coalesce(func.sum(Donation.amount), 0)).where(
        Donation.date >= last_year_month, Donation.date <= last_year_end))).scalar() or Decimal("1")
    giving_trend = float((month_giving - ly_giving) / max(ly_giving, Decimal("1"))) * 100
    unique_donors = (await db.execute(select(func.count(func.distinct(Donation.donor_id))).where(
        Donation.date >= month_start, Donation.donor_id.isnot(None)))).scalar() or 0

    # Groups
    active_groups = (await db.execute(select(func.count()).where(Group.is_active == True))).scalar() or 0
    total_gm = (await db.execute(select(func.count(GroupMembership.id)))).scalar() or 0

    return DashboardSummary(
        total_members=total_members, active_members=active_members,
        new_members_this_month=new_members, new_visitors_this_month=new_visitors,
        avg_weekly_attendance=round(avg_weekly, 1), last_sunday_attendance=last_sun,
        attendance_trend_percent=round(att_trend, 1),
        total_giving_this_month=month_giving, total_giving_ytd=ytd_giving,
        giving_trend_percent=round(giving_trend, 1), unique_donors_this_month=unique_donors,
        active_groups=active_groups, total_group_members=total_gm)


@router.get("/giving", response_model=GivingAnalytics)
async def giving_analytics(
    start_date: Optional[date] = None, end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pastor", "staff"))):
    if not start_date: start_date = date.today().replace(month=1, day=1)
    if not end_date: end_date = date.today()

    base = select(Donation).where(Donation.date >= start_date, Donation.date <= end_date)
    donations = (await db.execute(base.order_by(Donation.date))).scalars().all()
    total = sum(d.amount for d in donations)
    count = len(donations)
    donors = set(d.donor_id for d in donations if d.donor_id)

    # By fund
    fund_map = {}
    for d in donations:
        fund_map.setdefault(d.fund_id, {"total": Decimal("0"), "count": 0})
        fund_map[d.fund_id]["total"] += d.amount
        fund_map[d.fund_id]["count"] += 1
    by_fund = []
    for fid, data in fund_map.items():
        f = (await db.execute(select(Fund).where(Fund.id == fid))).scalar_one_or_none()
        by_fund.append(FundGivingSummary(fund_id=fid, fund_name=f.name if f else "Unknown",
                                          total=data["total"], count=data["count"]))

    # By type & method
    type_map, method_map = {}, {}
    for d in donations:
        type_map.setdefault(d.donation_type, {"total": Decimal("0"), "count": 0})
        type_map[d.donation_type]["total"] += d.amount; type_map[d.donation_type]["count"] += 1
        method_map.setdefault(d.payment_method, {"total": Decimal("0"), "count": 0})
        method_map[d.payment_method]["total"] += d.amount; method_map[d.payment_method]["count"] += 1

    recurring = len([d for d in donations if d.is_recurring])

    return GivingAnalytics(
        total_amount=total, donation_count=count, unique_donors=len(donors),
        avg_donation=total / count if count else Decimal("0"),
        by_fund=by_fund,
        by_type=[TypeGivingSummary(donation_type=k, total=v["total"], count=v["count"]) for k, v in type_map.items()],
        by_method=[MethodGivingSummary(payment_method=k, total=v["total"], count=v["count"]) for k, v in method_map.items()],
        lapsed_donors=0, first_time_donors=0, recurring_donors=recurring)


@router.get("/attendance", response_model=AttendanceAnalytics)
async def attendance_analytics(
    start_date: Optional[date] = None, end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pastor", "staff"))):
    if not start_date: start_date = date.today() - timedelta(days=90)
    if not end_date: end_date = date.today()

    total = (await db.execute(select(func.count()).where(
        AttendanceRecord.date >= start_date, AttendanceRecord.date <= end_date))).scalar() or 0
    days = max((end_date - start_date).days // 7, 1)
    avg = total / days

    peak_date_result = (await db.execute(
        select(AttendanceRecord.date, func.count().label("cnt"))
        .where(AttendanceRecord.date >= start_date, AttendanceRecord.date <= end_date)
        .group_by(AttendanceRecord.date).order_by(func.count().desc()).limit(1)
    )).first()
    peak_date = peak_date_result[0] if peak_date_result else None
    peak_count = peak_date_result[1] if peak_date_result else 0

    ftg = (await db.execute(select(func.count()).where(
        AttendanceRecord.date >= start_date, AttendanceRecord.date <= end_date,
        AttendanceRecord.is_first_time_guest == True))).scalar() or 0

    # By service
    services = (await db.execute(select(Service))).scalars().all()
    by_service = []
    for s in services:
        svc_count = (await db.execute(select(func.count()).where(
            AttendanceRecord.service_id == s.id,
            AttendanceRecord.date >= start_date, AttendanceRecord.date <= end_date))).scalar() or 0
        by_service.append(ServiceAttendanceSummary(
            service_id=s.id, service_name=s.name,
            avg_attendance=round(svc_count / max(days, 1), 1), total_records=svc_count))

    return AttendanceAnalytics(total_records=total, avg_attendance=round(avg, 1),
        peak_attendance=peak_count, peak_date=peak_date,
        by_service=by_service, first_time_guests_total=ftg)


@router.get("/financial", response_model=list[FinancialSummary])
async def financial_report(year: int = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pastor"))):
    if not year: year = date.today().year
    year_start = date(year, 1, 1); year_end = date(year, 12, 31)
    funds = (await db.execute(select(Fund))).scalars().all()
    items = []
    for f in funds:
        income = (await db.execute(select(func.coalesce(func.sum(Donation.amount), 0)).where(
            Donation.fund_id == f.id, Donation.date >= year_start, Donation.date <= year_end))).scalar()
        expenses = (await db.execute(select(func.coalesce(func.sum(Expense.amount), 0)).where(
            Expense.fund_id == f.id, Expense.date >= year_start, Expense.date <= year_end))).scalar()
        budget = (await db.execute(select(Budget).where(
            Budget.fund_id == f.id, Budget.fiscal_year == year))).scalar_one_or_none()
        budgeted = budget.budgeted_amount if budget else None
        variance = (income - expenses) - budgeted if budgeted else None
        items.append(FinancialSummary(
            fund_id=f.id, fund_name=f.name, fund_type=f.fund_type,
            total_income=income, total_expenses=expenses, net=income - expenses,
            budgeted=budgeted, budget_variance=variance, is_restricted=f.is_restricted))
    return items


@router.get("/export/{report_type}")
async def export_report(report_type: str, year: int = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pastor", "staff"))):
    out = io.StringIO(); w = csv.writer(out)
    if report_type == "members":
        w.writerow(["ID", "Name", "Email", "Phone", "Status", "Join Date"])
        for m in (await db.execute(select(Member).where(Member.is_deleted == False))).scalars().all():
            w.writerow([m.id, f"{m.first_name} {m.last_name}", m.email, m.phone, m.membership_status,
                        m.join_date.isoformat() if m.join_date else ""])
    elif report_type == "giving":
        w.writerow(["Date", "Donor", "Fund", "Amount", "Type", "Method"])
        for d in (await db.execute(select(Donation).order_by(Donation.date.desc()))).scalars().all():
            dn = fn = ""
            if d.donor_id:
                mem = (await db.execute(select(Member).where(Member.id == d.donor_id))).scalar_one_or_none()
                if mem: dn = f"{mem.first_name} {mem.last_name}"
            fund = (await db.execute(select(Fund).where(Fund.id == d.fund_id))).scalar_one_or_none()
            if fund: fn = fund.name
            w.writerow([d.date.isoformat(), dn, fn, float(d.amount), d.donation_type, d.payment_method])
    else:
        return {"error": f"Unknown report type: {report_type}. Use 'members' or 'giving'."}
    out.seek(0)
    return StreamingResponse(io.BytesIO(out.getvalue().encode()), media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={report_type}_report.csv"})


# ── Advanced Analytics (Phase 3) ──────────────────────────────


@router.get("/analytics/overview")
async def analytics_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pastor", "staff"))):
    """Church health metrics: membership, engagement, giving, events."""
    from app.models.feed import Post, PostLike, PostComment
    from app.models.chat import Message
    from app.models.event import Event, EventRSVP
    from app.models.prayer import PrayerRequest

    today = date.today()
    month_start = today.replace(day=1)
    cid = current_user.church_id

    total_members = (await db.execute(select(func.count()).where(
        Member.church_id == cid, Member.is_deleted == False))).scalar() or 0
    new_members = (await db.execute(select(func.count()).where(
        Member.church_id == cid, Member.is_deleted == False,
        Member.join_date >= month_start))).scalar() or 0

    month_giving = (await db.execute(
        select(func.coalesce(func.sum(Donation.amount), 0)).where(
            Donation.church_id == cid, Donation.date >= month_start)
    )).scalar() or 0

    posts_this_month = (await db.execute(select(func.count()).where(
        Post.church_id == cid, Post.created_at >= month_start))).scalar() or 0
    messages_this_month = (await db.execute(select(func.count()).where(
        Message.created_at >= month_start))).scalar() or 0

    upcoming_events = (await db.execute(select(func.count()).where(
        Event.church_id == cid, Event.is_cancelled == False,
        Event.start_datetime >= today))).scalar() or 0

    prayer_count = (await db.execute(select(func.count()).where(
        PrayerRequest.church_id == cid, PrayerRequest.is_deleted == False,
        PrayerRequest.created_at >= month_start))).scalar() or 0

    # Engagement score: weighted metric (0-100)
    max_members = max(total_members, 1)
    engagement = min(100, int(
        (posts_this_month * 2 + messages_this_month * 0.5 + prayer_count * 3) / max_members * 10
    ))

    return {
        "total_members": total_members,
        "new_members_this_month": new_members,
        "total_giving_this_month": float(month_giving),
        "posts_this_month": posts_this_month,
        "messages_this_month": messages_this_month,
        "upcoming_events": upcoming_events,
        "active_prayer_requests": prayer_count,
        "engagement_score": engagement,
    }


@router.get("/analytics/engagement")
async def analytics_engagement(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pastor", "staff"))):
    """Engagement breakdown: posts, likes, comments, chat activity, prayers."""
    from app.models.feed import Post, PostLike, PostComment
    from app.models.chat import Message, Conversation
    from app.models.prayer import PrayerRequest, PrayerResponseEntry

    today = date.today()
    cid = current_user.church_id

    # Last 4 weeks of engagement
    weeks = []
    for i in range(4):
        start = today - timedelta(weeks=i + 1)
        end = today - timedelta(weeks=i)
        posts = (await db.execute(select(func.count()).where(
            Post.church_id == cid, Post.created_at >= start, Post.created_at < end))).scalar() or 0
        comments = (await db.execute(select(func.count()).where(
            PostComment.created_at >= start, PostComment.created_at < end))).scalar() or 0
        prayers = (await db.execute(select(func.count()).where(
            PrayerRequest.church_id == cid,
            PrayerRequest.created_at >= start, PrayerRequest.created_at < end))).scalar() or 0
        weeks.append({
            "week": f"Week {i + 1}",
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "posts": posts,
            "comments": comments,
            "prayer_requests": prayers,
        })

    return {"weekly_engagement": weeks}


@router.get("/analytics/giving-trends")
async def analytics_giving_trends(
    year: int = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pastor"))):
    """Monthly giving trends with year-over-year comparison."""
    if not year:
        year = date.today().year
    cid = current_user.church_id

    months = []
    for m in range(1, 13):
        start = date(year, m, 1)
        if m == 12:
            end = date(year + 1, 1, 1)
        else:
            end = date(year, m + 1, 1)

        current = (await db.execute(
            select(func.coalesce(func.sum(Donation.amount), 0)).where(
                Donation.church_id == cid,
                Donation.date >= start, Donation.date < end)
        )).scalar() or 0

        # Previous year same month
        py_start = date(year - 1, m, 1)
        if m == 12:
            py_end = date(year, 1, 1)
        else:
            py_end = date(year - 1, m + 1, 1)
        previous = (await db.execute(
            select(func.coalesce(func.sum(Donation.amount), 0)).where(
                Donation.church_id == cid,
                Donation.date >= py_start, Donation.date < py_end)
        )).scalar() or 0

        months.append({
            "month": start.strftime("%B"),
            "current_year": float(current),
            "previous_year": float(previous),
            "yoy_change_pct": round(
                float((current - previous) / max(previous, 1)) * 100, 1
            ) if previous else None,
        })

    summary = {"year": year, "monthly_trends": months}
    return summary


@router.get("/tax-statements")
async def get_tax_statements(
    year: int = Query(None, description="Year to generate statements for"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pastor", "staff", "finance_team")),
):
    """
    Generate downloadable yearly CSV tax receipts for active donors.
    """
    target_year = year or (date.today().year - 1)
    
    start_date = date(target_year, 1, 1)
    end_date = date(target_year, 12, 31)

    # Fetch all donations in the year
    query = select(Donation, Member).join(Member).where(
        Donation.church_id == current_user.church_id,
        Donation.date >= start_date,
        Donation.date <= end_date,
        Donation.donor_id.isnot(None)
    )
    result = await db.execute(query)
    records = result.all()

    # Aggregate by donor
    donor_totals = {}
    for donation, member in records:
        if member.id not in donor_totals:
            donor_totals[member.id] = {
                "name": f"{member.first_name} {member.last_name}",
                "email": member.email or "",
                "address": f"{member.address or ''} {member.city or ''} {member.state or ''} {member.zip_code or ''}".strip(),
                "total": Decimal("0.0")
            }
        donor_totals[member.id]["total"] += donation.amount

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Donor ID", "Name", "Email", "Address", f"Total Amount ({target_year})", "Tax Deductible"])
    
    for donor_id, data in donor_totals.items():
        writer.writerow([donor_id, data["name"], data["email"], data["address"], format(data["total"], ".2f"), "Yes"])
        
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=tax_statements_{target_year}.csv"}
    )


@router.get("/analytics/growth")
async def analytics_growth(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pastor"))):
    """Membership growth funnel: visitor → prospect → member."""
    cid = current_user.church_id
    today = date.today()

    visitors = (await db.execute(select(func.count()).where(
        Member.church_id == cid, Member.membership_status == "visitor",
        Member.is_deleted == False))).scalar() or 0
    prospects = (await db.execute(select(func.count()).where(
        Member.church_id == cid, Member.membership_status == "prospect",
        Member.is_deleted == False))).scalar() or 0
    active = (await db.execute(select(func.count()).where(
        Member.church_id == cid,
        Member.membership_status.in_(["active", "member"]),
        Member.is_deleted == False))).scalar() or 0
    inactive = (await db.execute(select(func.count()).where(
        Member.church_id == cid, Member.membership_status == "inactive",
        Member.is_deleted == False))).scalar() or 0

    # Monthly growth for last 6 months
    monthly = []
    for i in range(6):
        month_start = (today.replace(day=1) - timedelta(days=30 * i)).replace(day=1)
        if month_start.month == 12:
            month_end = date(month_start.year + 1, 1, 1)
        else:
            month_end = date(month_start.year, month_start.month + 1, 1)
        new = (await db.execute(select(func.count()).where(
            Member.church_id == cid, Member.is_deleted == False,
            Member.join_date >= month_start, Member.join_date < month_end
        ))).scalar() or 0
        monthly.append({
            "month": month_start.strftime("%B %Y"),
            "new_members": new,
        })

    return {
        "funnel": {
            "visitors": visitors,
            "prospects": prospects,
            "active_members": active,
            "inactive_members": inactive,
        },
        "monthly_growth": list(reversed(monthly)),
    }


@router.get("/financial-summary")
async def financial_summary(
    period: str = Query("month", regex="^(week|month|quarter|year)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pastor"))):
    """Get financial summary: income, expenses, balance."""
    from datetime import timezone as tz
    from datetime import datetime

    today = date.today()
    cid = current_user.church_id

    if period == "week":
        start = today - timedelta(weeks=1)
    elif period == "quarter":
        start = today - timedelta(days=90)
    elif period == "year":
        start = today - timedelta(days=365)
    else:
        start = today.replace(day=1)

    # Total income
    income = (await db.execute(
        select(func.coalesce(func.sum(Donation.amount), 0)).where(
            Donation.church_id == cid,
            Donation.date >= start,
        )
    )).scalar() or 0

    # Total expenses
    expenses = (await db.execute(
        select(func.coalesce(func.sum(Expense.amount), 0)).where(
            Expense.church_id == cid,
            Expense.date >= start,
        )
    )).scalar() or 0

    return {"data": {
        "period": period,
        "start_date": start.isoformat(),
        "end_date": today.isoformat(),
        "total_income": float(income),
        "total_expenses": float(expenses),
        "net_balance": float(income) - float(expenses),
    }}

