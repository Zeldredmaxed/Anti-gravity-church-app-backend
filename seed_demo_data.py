"""
🌱 Demo Data Seed Script — Anti-Gravity Church Management System
═══════════════════════════════════════════════════════════════════
Seeds 5 realistic profiles + their full relational data:
  1. Marcus Sterling  — Highly engaged leader (Groups, Volunteers, Recurring Giving)
  2. Chloe Vance      — At-risk / fading member (AI Alerts, Automated Tasks)
  3. Julian Hayes     — First-time guest with urgent need (Care Board, Prayer)
  4. Evelyn Cho       — Generous but uninvolved donor (Financial Analytics)
  5. The Miller Family — Eager family (Households, Child Check-In, Volunteer App)

Usage:
  python seed_demo_data.py
"""

import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from app.database import engine, async_session, Base
from app.models.user import User
from app.models.church import Church
from app.models.member import Member
from app.models.family import Family, FamilyRelationship
from app.models.group import Group, GroupMembership
from app.models.fund import Fund
from app.models.donation import Donation, Pledge
from app.models.attendance import Service, AttendanceRecord
from app.models.child_checkin import CheckinSession
from app.models.volunteer import VolunteerRole, VolunteerSchedule, VolunteerApplication, VolunteerHoursLog
from app.models.care import CareCase, CareNote
from app.models.task import MinistryTask
from app.models.prayer import PrayerRequest
from app.models.activity_log import MemberActivityLog
from app.models.alert import Alert
from app.utils.security import hash_password

from sqlalchemy import select, func


NOW = datetime.now(timezone.utc)
TODAY = date.today()


async def get_or_create_church(session):
    """Get existing church or create demo church."""
    result = await session.execute(select(Church).where(Church.subdomain == "newbirthfellowship"))
    church = result.scalar_one_or_none()
    if not church:
        # Fallback: check any existing church
        result = await session.execute(select(Church).limit(1))
        church = result.scalar_one_or_none()
    if church:
        print(f"  ✅ Using existing church: {church.name} (id={church.id})")
        return church

    church = Church(
        name="New Birth Fellowship",
        subdomain="newbirthfellowship",
        description="A vibrant community of faith, dedicated to spiritual growth and outreach.",
        pastor_name="Pastor Jeremiah Cole",
        address="4200 Grace Blvd, Atlanta, GA 30331",
        phone="(404) 555-9900",
        email="info@newbirthfellowship.org",
        website="https://newbirthfellowship.org",
        latitude=33.7490,
        longitude=-84.3880,
    )
    session.add(church)
    await session.flush()
    await session.refresh(church)
    print(f"  🏛️  Created church: {church.name} (id={church.id})")
    return church


async def get_or_create_admin_user(session, church_id):
    """Get existing admin user or create one for relational seeding."""
    result = await session.execute(
        select(User).where(User.church_id == church_id, User.role == "admin").limit(1)
    )
    user = result.scalar_one_or_none()
    if user:
        print(f"  ✅ Using existing admin user: {user.full_name} (id={user.id})")
        return user

    user = User(
        church_id=church_id,
        email="admin@newbirthfellowship.org",
        hashed_password=hash_password("Admin123!"),
        full_name="Pastor Jeremiah Cole",
        role="admin",
        is_active=True,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    print(f"  👤 Created admin user: {user.full_name} (id={user.id})")
    return user


async def create_funds(session, church_id):
    """Create essential giving funds."""
    fund_defs = [
        {"name": "General Tithe Fund", "fund_type": "general", "target_amount": Decimal("120000.00")},
        {"name": "Building Fund", "fund_type": "building", "target_amount": Decimal("500000.00"), "is_restricted": True},
        {"name": "Missions Fund", "fund_type": "missions", "target_amount": Decimal("30000.00")},
        {"name": "Youth Ministry Fund", "fund_type": "youth", "target_amount": Decimal("15000.00")},
        {"name": "Benevolence Fund", "fund_type": "benevolence", "target_amount": Decimal("10000.00")},
    ]
    funds = {}
    for fd in fund_defs:
        existing = (await session.execute(
            select(Fund).where(Fund.church_id == church_id, Fund.name == fd["name"])
        )).scalar_one_or_none()
        if existing:
            funds[fd["fund_type"]] = existing
            continue
        fund = Fund(church_id=church_id, current_balance=Decimal("0.00"), **fd)
        session.add(fund)
        await session.flush()
        await session.refresh(fund)
        funds[fd["fund_type"]] = fund
    print(f"  💰 Funds ready: {', '.join(f.name for f in funds.values())}")
    return funds


async def create_service(session, church_id):
    """Create a Sunday Morning service."""
    existing = (await session.execute(
        select(Service).where(Service.church_id == church_id, Service.name == "Sunday Morning Worship")
    )).scalar_one_or_none()
    if existing:
        print(f"  ✅ Using existing service: {existing.name} (id={existing.id})")
        return existing

    svc = Service(
        church_id=church_id,
        name="Sunday Morning Worship",
        service_type="sunday_morning",
        day_of_week="Sunday",
        start_time="10:00",
        is_active=True,
    )
    session.add(svc)
    await session.flush()
    await session.refresh(svc)
    print(f"  ⛪ Created service: {svc.name} (id={svc.id})")
    return svc


async def create_volunteer_roles(session, church_id):
    """Create volunteer roles needed by the demo profiles."""
    role_defs = [
        {"name": "Bass Guitar", "description": "Plays bass guitar during worship services.", "teams": "Worship Team", "capacity_needed": 2},
        {"name": "Nursery Team", "description": "Provides loving care for infants and toddlers during services.", "teams": "Children's Ministry", "capacity_needed": 6},
        {"name": "Usher", "description": "Welcomes guests and assists with seating.", "teams": "Hospitality Team", "capacity_needed": 8},
        {"name": "Sound Tech", "description": "Manages audio equipment during services.", "teams": "Media Team", "capacity_needed": 3},
    ]
    roles = {}
    for rd in role_defs:
        existing = (await session.execute(
            select(VolunteerRole).where(VolunteerRole.church_id == church_id, VolunteerRole.name == rd["name"])
        )).scalar_one_or_none()
        if existing:
            roles[rd["name"]] = existing
            continue
        role = VolunteerRole(church_id=church_id, is_active=True, **rd)
        session.add(role)
        await session.flush()
        await session.refresh(role)
        roles[rd["name"]] = role
    print(f"  🎵 Volunteer roles ready: {', '.join(roles.keys())}")
    return roles


# ═══════════════════════════════════════════════════════════════════════════════
# PROFILE SEEDERS
# ═══════════════════════════════════════════════════════════════════════════════

async def seed_marcus_sterling(session, church_id, admin_user_id, funds, service, vol_roles):
    """
    Profile 1: Marcus Sterling — Highly Engaged Leader
    Tests: Groups, Volunteers, Recurring Giving, KPI cards
    """
    print("\n  🧔 Seeding Profile 1: Marcus Sterling (Engaged Leader)...")

    # ── Member ──
    marcus = Member(
        church_id=church_id,
        first_name="Marcus", last_name="Sterling",
        email="marcus.s@example.com", phone="+1 (555) 019-8822",
        gender="male", date_of_birth=date(1984, 5, 12),
        address="1822 Covenant Lane", city="Atlanta", state="GA", zip_code="30318",
        membership_status="active", join_date=date(2014, 9, 1),
        baptism_date=date(2015, 4, 12), baptism_type="immersion",
        baptism_location="New Birth Fellowship", baptism_pastor="Pastor J. Cole",
        salvation_status="saved", salvation_date=date(2014, 6, 1),
        completed_membership_class=True, membership_class_date=date(2014, 11, 15),
        health_score=95, health_status="engaged",
        skills_tags=["Bass Guitar", "Music Production", "Leadership"],
        interests=["Worship Ministry", "Men's Ministry", "Discipleship"],
        marital_status="married",
    )
    session.add(marcus)
    await session.flush()
    await session.refresh(marcus)

    # ── Small Group (leader) ──
    group = Group(
        church_id=church_id,
        name="Men's Dawn Breakers",
        description="Weekly men's group focused on accountability, prayer, and spiritual growth. Meets Saturday mornings.",
        group_type="mens_group",
        leader_id=marcus.id,
        meeting_day="Saturday",
        meeting_time="06:30",
        meeting_location="Fellowship Hall - Room B",
        is_active=True,
        max_capacity=15,
    )
    session.add(group)
    await session.flush()
    await session.refresh(group)

    # Add Marcus as leader member of the group
    gm = GroupMembership(
        group_id=group.id, member_id=marcus.id,
        role="leader", joined_date=date(2020, 1, 10),
    )
    session.add(gm)

    # ── Recurring Tithe Donations (last 6 months — $500/month) ──
    general_fund = funds["general"]
    for i in range(6):
        month_date = (NOW - timedelta(days=30 * i)).date().replace(day=1)
        don = Donation(
            church_id=church_id,
            donor_id=marcus.id,
            fund_id=general_fund.id,
            amount=Decimal("500.00"),
            donation_type="tithe",
            payment_method="bank_transfer",
            date=month_date,
            is_recurring=True,
            recurring_frequency="monthly",
            status="completed",
            notes="ACH auto-debit"
        )
        session.add(don)
    # Update fund balance
    general_fund.current_balance = (general_fund.current_balance or Decimal("0")) + Decimal("3000.00")

    # ── Volunteer: Bass Guitar (Worship Team) ──
    bass_role = vol_roles["Bass Guitar"]
    schedule = VolunteerSchedule(
        church_id=church_id,
        role_id=bass_role.id,
        member_id=marcus.id,
        service_id=service.id,
        start_time=NOW.replace(hour=9, minute=0),
        end_time=NOW.replace(hour=12, minute=0),
        status="confirmed",
    )
    session.add(schedule)
    await session.flush()

    # ── Hours Logged (4 Sundays this month × 3 hours = 12 hours) ──
    for week in range(4):
        log = VolunteerHoursLog(
            church_id=church_id,
            member_id=marcus.id,
            role_id=bass_role.id,
            hours_served=Decimal("3.00"),
            date=TODAY - timedelta(weeks=week),
            notes="Sunday morning worship service",
            logged_by=admin_user_id,
        )
        session.add(log)

    # ── Attendance (last 8 Sundays — perfect attendance) ──
    for week in range(8):
        att_date = TODAY - timedelta(weeks=week)
        att = AttendanceRecord(
            church_id=church_id,
            member_id=marcus.id,
            service_id=service.id,
            date=att_date,
            check_in_time=NOW - timedelta(weeks=week, hours=2),
            is_first_time_guest=False,
        )
        session.add(att)

    # ── Activity Timeline ──
    activities = [
        ("baptism", "Baptized by immersion at New Birth Fellowship", date(2015, 4, 12)),
        ("volunteer_started", "Joined Worship Team as Bass Guitar player", date(2018, 3, 1)),
        ("joined_group", "Became leader of Men's Dawn Breakers small group", date(2020, 1, 10)),
        ("milestone", "Completed Advanced Discipleship Track", date(2021, 6, 15)),
    ]
    for atype, desc, odate in activities:
        log = MemberActivityLog(
            church_id=church_id, member_id=marcus.id,
            activity_type=atype, description=desc,
            occurred_at=datetime.combine(odate, datetime.min.time()).replace(tzinfo=timezone.utc),
        )
        session.add(log)

    await session.flush()
    print(f"    ✅ Marcus Sterling seeded (member_id={marcus.id})")
    print(f"       → Group: 'Men's Dawn Breakers' (group_id={group.id})")
    print(f"       → 6 recurring donations ($500/mo)")
    print(f"       → 12 volunteer hours, 8 attendance records")
    return marcus


async def seed_chloe_vance(session, church_id, admin_user_id, service):
    """
    Profile 2: Chloe Vance — At-Risk / Fading Member
    Tests: AI Alerts, Automated Tasks, At-Risk KPI
    """
    print("\n  👩 Seeding Profile 2: Chloe Vance (At-Risk Member)...")

    chloe = Member(
        church_id=church_id,
        first_name="Chloe", last_name="Vance",
        email="chloe.v@example.com", phone="+1 (555) 019-3341",
        gender="female", date_of_birth=date(1998, 8, 22),
        address="910 Summit Ridge Dr", city="Decatur", state="GA", zip_code="30030",
        membership_status="active", join_date=date(2021, 3, 15),
        baptism_date=date(2022, 6, 19), baptism_type="immersion",
        salvation_status="saved", salvation_date=date(2021, 5, 1),
        health_score=18, health_status="at_risk",
        skills_tags=["Social Media", "Photography"],
        interests=["Young Adults Ministry", "Creative Arts"],
        marital_status="single",
    )
    session.add(chloe)
    await session.flush()
    await session.refresh(chloe)

    # ── Attendance: Last attended 5 weeks ago, then attended regularly before ──
    # Weeks 1-4 ago: ABSENT (missed 4 consecutive Sundays)
    # Weeks 5-12 ago: Present (was regular before dropping off)
    for week in range(5, 13):
        att = AttendanceRecord(
            church_id=church_id,
            member_id=chloe.id,
            service_id=service.id,
            date=TODAY - timedelta(weeks=week),
            check_in_time=NOW - timedelta(weeks=week, hours=2),
            is_first_time_guest=False,
        )
        session.add(att)

    # ── Automated Follow-Up Task ──
    task = MinistryTask(
        church_id=church_id,
        assigned_to=admin_user_id,
        assigned_by=admin_user_id,
        related_member_id=chloe.id,
        title="Follow up with Chloe Vance (Missed 4 Weeks)",
        description="Chloe Vance has missed the last 4 consecutive Sundays. Previously was a consistent attender. Please reach out to check on her well-being and encourage her return.",
        task_type="follow_up",
        action_type="log_call",
        status="pending",
        due_date=NOW + timedelta(days=3),
    )
    session.add(task)

    # ── Alert for dashboard ──
    alert = Alert(
        church_id=church_id,
        user_id=admin_user_id,
        type="system",
        title="⚠️ At-Risk Member: Chloe Vance",
        body="Chloe Vance has missed 4 consecutive Sundays. Health score dropped to 18. Automated follow-up task created.",
        is_read=False,
    )
    session.add(alert)

    # ── Activity Timeline ──
    logs = [
        ("baptism", "Baptized by immersion at New Birth Fellowship", date(2022, 6, 19)),
        ("membership_change", "Membership status: Active", date(2021, 3, 15)),
    ]
    for atype, desc, odate in logs:
        log = MemberActivityLog(
            church_id=church_id, member_id=chloe.id,
            activity_type=atype, description=desc,
            occurred_at=datetime.combine(odate, datetime.min.time()).replace(tzinfo=timezone.utc),
        )
        session.add(log)

    await session.flush()
    print(f"    ✅ Chloe Vance seeded (member_id={chloe.id})")
    print(f"       → Health Score: 🔴 18 (At-Risk)")
    print(f"       → Missed last 4 Sundays, 8 prior attendance records")
    print(f"       → Auto-generated follow-up task (pending)")
    return chloe


async def seed_julian_hayes(session, church_id, admin_user_id, service):
    """
    Profile 3: Julian Hayes — First-Time Guest with Urgent Care Need
    Tests: Care Board, Prayer Requests, First-Time Guest Metric
    """
    print("\n  🧑 Seeding Profile 3: Julian Hayes (First-Time Guest)...")

    julian = Member(
        church_id=church_id,
        first_name="Julian", last_name="Hayes",
        email="j.hayes@example.com", phone="+1 (555) 019-7711",
        gender="male", date_of_birth=date(1991, 11, 3),
        address="2305 Peachtree Industrial Blvd", city="Duluth", state="GA", zip_code="30097",
        membership_status="visitor",
        salvation_status="not_saved",
        health_score=45, health_status="new",
        marital_status="single",
    )
    session.add(julian)
    await session.flush()
    await session.refresh(julian)

    # ── First-Time Attendance (last Sunday) ──
    last_sunday = TODAY - timedelta(days=TODAY.weekday() + 1)  # Most recent Sunday
    if last_sunday > TODAY:
        last_sunday -= timedelta(weeks=1)

    att = AttendanceRecord(
        church_id=church_id,
        member_id=julian.id,
        service_id=service.id,
        date=last_sunday,
        check_in_time=datetime.combine(last_sunday, datetime.min.time()).replace(hour=10, minute=5, tzinfo=timezone.utc),
        is_first_time_guest=True,
        guest_info={"source": "friend_invite", "notes": "Came with neighbor, seemed emotionally distressed"},
    )
    session.add(att)

    # ── Care Case: URGENT / NEW ──
    care_case = CareCase(
        church_id=church_id,
        requester_name="Julian Hayes",
        member_id=julian.id,
        care_type="Care",
        sub_type="Hospice / End of Life",
        summary="Mother was just moved to hospice care this week. Julian came to church for the first time seeking prayer and comfort. He requested a pastoral call and prayer support during this difficult time. He is not saved and appeared very emotional during the service.",
        priority="urgent",
        status="NEW",
        assigned_leader_id=admin_user_id,
    )
    session.add(care_case)
    await session.flush()
    await session.refresh(care_case)

    # ── Care Note (initial intake) ──
    note = CareNote(
        care_case_id=care_case.id,
        author_id=admin_user_id,
        content="First-time visitor Julian Hayes attended Sunday service and filled out a prayer card. His mother was recently moved to hospice. He's asking for pastoral support and prayer. Not currently saved. Please prioritize pastoral outreach this week.",
        action_taken="Prayer Card Received",
    )
    session.add(note)

    # ── Prayer Request ──
    prayer = PrayerRequest(
        church_id=church_id,
        author_id=admin_user_id,
        title="Urgent: Julian Hayes — Mother in Hospice",
        description="First-time guest Julian Hayes is going through an incredibly difficult time. His mother was just moved to hospice care. Please lift Julian and his family up in prayer for comfort, peace, and God's presence during this season.",
        category="healing",
        is_urgent=True,
        visibility="church_only",
        prayed_count=3,
    )
    session.add(prayer)

    # ── Task: Pastoral follow-up ──
    task = MinistryTask(
        church_id=church_id,
        assigned_to=admin_user_id,
        assigned_by=admin_user_id,
        related_member_id=julian.id,
        care_case_id=care_case.id,
        title="Pastoral Call — Julian Hayes (First-Time Guest, Urgent)",
        description="Julian is a first-time guest whose mother is in hospice. He requested a pastoral call. This is a high-priority care opportunity. Call within 24 hours.",
        task_type="pastoral_care",
        action_type="log_call",
        status="pending",
        due_date=NOW + timedelta(days=1),
    )
    session.add(task)

    # ── Activity Timeline ──
    log = MemberActivityLog(
        church_id=church_id, member_id=julian.id,
        activity_type="care_case_opened",
        description="Urgent care case opened: Mother moved to hospice. Requesting prayer and pastoral call.",
        occurred_at=NOW - timedelta(hours=6),
    )
    session.add(log)

    await session.flush()
    print(f"    ✅ Julian Hayes seeded (member_id={julian.id})")
    print(f"       → First-time guest attendance (last Sunday)")
    print(f"       → URGENT care case (care_case_id={care_case.id})")
    print(f"       → Prayer request + pastoral follow-up task")
    return julian


async def seed_evelyn_cho(session, church_id, admin_user_id, funds, service):
    """
    Profile 4: Evelyn Cho — Generous but Uninvolved Donor
    Tests: Financial Analytics, Giving Charts, Large Donations
    """
    print("\n  👩‍💼 Seeding Profile 4: Evelyn Cho (Big Donor)...")

    evelyn = Member(
        church_id=church_id,
        first_name="Evelyn", last_name="Cho",
        email="echo.design@example.com", phone="+1 (555) 019-9900",
        gender="female", date_of_birth=date(1965, 2, 14),
        address="8850 Northpoint Pkwy", city="Alpharetta", state="GA", zip_code="30022",
        membership_status="active", join_date=date(2019, 1, 10),
        salvation_status="saved",
        health_score=60, health_status="inconsistent",
        skills_tags=["Interior Design", "Event Planning"],
        interests=["Building Committee"],
        marital_status="widowed",
    )
    session.add(evelyn)
    await session.flush()
    await session.refresh(evelyn)

    # ── HUGE One-Time Donation: $15,000 to Building Fund (Check) ──
    building_fund = funds["building"]
    big_donation = Donation(
        church_id=church_id,
        donor_id=evelyn.id,
        fund_id=building_fund.id,
        amount=Decimal("15000.00"),
        donation_type="building",
        payment_method="check",
        check_number="4488",
        date=TODAY - timedelta(days=5),
        is_recurring=False,
        status="completed",
        notes="One-time contribution to Building Fund expansion campaign",
    )
    session.add(big_donation)
    building_fund.current_balance = (building_fund.current_balance or Decimal("0")) + Decimal("15000.00")

    # ── Small regular tithes (once per month, $200 — 4 months history) ──
    general_fund = funds["general"]
    for i in range(4):
        mon = (NOW - timedelta(days=30 * (i + 1))).date().replace(day=15)
        don = Donation(
            church_id=church_id,
            donor_id=evelyn.id,
            fund_id=general_fund.id,
            amount=Decimal("200.00"),
            donation_type="offering",
            payment_method="online",
            date=mon,
            status="completed",
        )
        session.add(don)
    general_fund.current_balance = (general_fund.current_balance or Decimal("0")) + Decimal("800.00")

    # ── Pledge to Building Fund ──
    pledge = Pledge(
        church_id=church_id,
        member_id=evelyn.id,
        fund_id=building_fund.id,
        campaign_name="Building Expansion Campaign 2026",
        pledged_amount=Decimal("25000.00"),
        fulfilled_amount=Decimal("15000.00"),  # 60% fulfilled
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        status="active",
        notes="Remaining balance to be fulfilled quarterly",
    )
    session.add(pledge)

    # ── Sparse Attendance (once a month for last 3 months) ──
    for i in range(3):
        att_date = (TODAY - timedelta(days=30 * (i + 1)))
        att = AttendanceRecord(
            church_id=church_id,
            member_id=evelyn.id,
            service_id=service.id,
            date=att_date,
            check_in_time=datetime.combine(att_date, datetime.min.time()).replace(hour=10, minute=15, tzinfo=timezone.utc),
            is_first_time_guest=False,
        )
        session.add(att)

    # ── Activity Timeline ──
    log = MemberActivityLog(
        church_id=church_id, member_id=evelyn.id,
        activity_type="donation",
        description="$15,000 donation to Building Fund (Check #4488)",
        occurred_at=NOW - timedelta(days=5),
    )
    session.add(log)

    await session.flush()
    print(f"    ✅ Evelyn Cho seeded (member_id={evelyn.id})")
    print(f"       → $15,000 Building Fund donation (spike for charts!)")
    print(f"       → $800 in regular offerings (4 months)")
    print(f"       → Pledge: $25K campaign, 60% fulfilled")
    print(f"       → Only 3 attendance records (low attendance, high giving)")
    return evelyn


async def seed_miller_family(session, church_id, admin_user_id, service, vol_roles):
    """
    Profile 5: The Miller Family — Sam, Jessica, Leo (4), Maya (2)
    Tests: Households, Child Check-In, Volunteer Applications
    """
    print("\n  👨‍👩‍👧‍👦 Seeding Profile 5: The Miller Family...")

    # ── Create Family ──
    family = Family(
        church_id=church_id,
        family_name="The Miller Family",
        address="3305 Rosewood Ct",
        city="Marietta", state="GA", zip_code="30062",
        phone="+1 (555) 019-1100",
    )
    session.add(family)
    await session.flush()
    await session.refresh(family)

    # ── Sam Miller (Head of Household) ──
    sam = Member(
        church_id=church_id, family_id=family.id,
        first_name="Sam", last_name="Miller",
        email="sam.miller@example.com", phone="+1 (555) 019-1101",
        gender="male", date_of_birth=date(1992, 3, 18),
        address="3305 Rosewood Ct", city="Marietta", state="GA", zip_code="30062",
        membership_status="active", join_date=date(2022, 9, 1),
        baptism_date=date(2023, 1, 8), baptism_type="immersion",
        salvation_status="saved",
        health_score=82, health_status="engaged",
        skills_tags=["Small Groups", "Setup/Teardown"],
        interests=["Family Ministry", "Men's Ministry"],
        marital_status="married",
        emergency_contact_name="Jessica Miller",
        emergency_contact_phone="+1 (555) 019-1102",
    )
    session.add(sam)

    # ── Jessica Miller (Spouse) ──
    jessica = Member(
        church_id=church_id, family_id=family.id,
        first_name="Jessica", last_name="Miller",
        email="jessica.miller@example.com", phone="+1 (555) 019-1102",
        gender="female", date_of_birth=date(1993, 7, 25),
        address="3305 Rosewood Ct", city="Marietta", state="GA", zip_code="30062",
        membership_status="active", join_date=date(2022, 9, 1),
        baptism_date=date(2023, 1, 8), baptism_type="immersion",
        salvation_status="saved",
        health_score=78, health_status="engaged",
        skills_tags=["Childcare", "Event Planning", "Hospitality"],
        interests=["Nursery Ministry", "Women's Ministry"],
        marital_status="married",
        emergency_contact_name="Sam Miller",
        emergency_contact_phone="+1 (555) 019-1101",
    )
    session.add(jessica)

    # ── Leo Miller (4 years old — child) ──
    leo = Member(
        church_id=church_id, family_id=family.id,
        first_name="Leo", last_name="Miller",
        gender="male", date_of_birth=date(2022, 1, 10),
        membership_status="active",
        health_score=100, health_status="engaged",
        emergency_contact_name="Sam Miller",
        emergency_contact_phone="+1 (555) 019-1101",
    )
    session.add(leo)

    # ── Maya Miller (2 years old — child) ──
    maya = Member(
        church_id=church_id, family_id=family.id,
        first_name="Maya", last_name="Miller",
        gender="female", date_of_birth=date(2024, 4, 5),
        membership_status="active",
        health_score=100, health_status="engaged",
        emergency_contact_name="Jessica Miller",
        emergency_contact_phone="+1 (555) 019-1102",
    )
    session.add(maya)

    await session.flush()
    for m in [sam, jessica, leo, maya]:
        await session.refresh(m)

    # ── Family Relationships ──
    rels = [
        FamilyRelationship(family_id=family.id, member_id=sam.id, relationship_type="head"),
        FamilyRelationship(family_id=family.id, member_id=jessica.id, relationship_type="spouse"),
        FamilyRelationship(family_id=family.id, member_id=leo.id, relationship_type="child"),
        FamilyRelationship(family_id=family.id, member_id=maya.id, relationship_type="child"),
    ]
    session.add_all(rels)

    # ── Attendance for Sam & Jessica (last 6 Sundays — weekly attenders) ──
    for week in range(6):
        att_date = TODAY - timedelta(weeks=week)
        for member in [sam, jessica]:
            att = AttendanceRecord(
                church_id=church_id,
                member_id=member.id,
                service_id=service.id,
                date=att_date,
                check_in_time=datetime.combine(att_date, datetime.min.time()).replace(hour=9, minute=50, tzinfo=timezone.utc),
                is_first_time_guest=False,
            )
            session.add(att)

    # ── Child Check-Ins (last Sunday — Leo → Pre-K, Maya → Nursery) ──
    last_sunday = TODAY - timedelta(days=TODAY.weekday() + 1)
    if last_sunday > TODAY:
        last_sunday -= timedelta(weeks=1)

    leo_checkin = CheckinSession(
        church_id=church_id,
        child_id=leo.id,
        service_id=service.id,
        parent_matching_id="MILLER-L-4488",
        checkin_time=datetime.combine(last_sunday, datetime.min.time()).replace(hour=9, minute=45, tzinfo=timezone.utc),
        checkout_time=datetime.combine(last_sunday, datetime.min.time()).replace(hour=12, minute=10, tzinfo=timezone.utc),
        room_assignment="Pre-K Room (Room 104)",
        alerts="No allergies. Parent pickup only.",
        checked_in_by=admin_user_id,
        checked_out_by=admin_user_id,
    )
    maya_checkin = CheckinSession(
        church_id=church_id,
        child_id=maya.id,
        service_id=service.id,
        parent_matching_id="MILLER-M-4489",
        checkin_time=datetime.combine(last_sunday, datetime.min.time()).replace(hour=9, minute=45, tzinfo=timezone.utc),
        checkout_time=datetime.combine(last_sunday, datetime.min.time()).replace(hour=12, minute=5, tzinfo=timezone.utc),
        room_assignment="Nursery (Room 101)",
        alerts="Pacifier in diaper bag. No food allergies.",
        checked_in_by=admin_user_id,
        checked_out_by=admin_user_id,
    )
    session.add_all([leo_checkin, maya_checkin])

    # ── Jessica's Pending Volunteer Application (Nursery Team) ──
    nursery_role = vol_roles["Nursery Team"]
    app = VolunteerApplication(
        church_id=church_id,
        member_id=jessica.id,
        role_id=nursery_role.id,
        status="pending",
        message="Hi! I'm Jessica Miller. My two kids (Leo, 4 and Maya, 2) attend every Sunday. I love working with children and would love to serve in the Nursery Team. I have 3 years of childcare experience and CPR certification.",
    )
    session.add(app)

    # ── Activity Timeline ──
    for m, desc in [(sam, "Sam & Jessica Miller joined the church together"), (jessica, "Joined alongside husband Sam")]:
        log = MemberActivityLog(
            church_id=church_id, member_id=m.id,
            activity_type="membership_change", description=desc,
            occurred_at=datetime.combine(date(2022, 9, 1), datetime.min.time()).replace(tzinfo=timezone.utc),
        )
        session.add(log)

    await session.flush()
    print(f"    ✅ Miller Family seeded (family_id={family.id})")
    print(f"       → Sam (id={sam.id}), Jessica (id={jessica.id})")
    print(f"       → Leo (id={leo.id}, age 4), Maya (id={maya.id}, age 2)")
    print(f"       → 2 child check-in sessions (Pre-K + Nursery)")
    print(f"       → Jessica's volunteer application: PENDING (Nursery Team)")
    return sam, jessica, leo, maya


# ═══════════════════════════════════════════════════════════════════════════════
# EXTRA: Background Donation History for Chart Testing
# ═══════════════════════════════════════════════════════════════════════════════

async def seed_historical_donations(session, church_id, funds):
    """Seed 12 months of aggregate giving data so charts have real shape."""
    print("\n  📊 Seeding 12-month historical giving (for chart testing)...")

    general_fund = funds["general"]
    # Monthly totals that create a realistic curve (seasonal patterns)
    monthly_totals = [
        (1, 8500), (2, 7200), (3, 9100), (4, 11000),  # Q1 - Easter spike
        (5, 7800), (6, 6900), (7, 6500), (8, 7100),    # Q2-Q3 summer dip
        (9, 8800), (10, 9500), (11, 10200), (12, 14500) # Q4 - year-end spike
    ]

    for month, total in monthly_totals:
        year = 2025 if month > NOW.month else 2026
        if year == 2026 and month > NOW.month:
            year = 2025  # Only seed past months
        don = Donation(
            church_id=church_id,
            donor_id=None,  # Anonymous aggregate
            fund_id=general_fund.id,
            amount=Decimal(str(total)),
            donation_type="offering",
            payment_method="online",
            date=date(year, month, 15),
            is_anonymous=True,
            status="completed",
            notes=f"Aggregated church giving for {year}-{month:02d}",
        )
        session.add(don)

    await session.flush()
    print(f"    ✅ 12 months of historical giving seeded (for trend charts)")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    print("=" * 65)
    print("Anti-Gravity ChMS -- Demo Data Seed Script")
    print("=" * 65)

    # The SQLite schema is far out of date -- many new columns were added to models.
    # Safest approach: back up old DB, recreate fresh from current models.
    import shutil
    db_path = os.path.join(os.path.dirname(__file__), "newbirth_church.db")
    
    # Dispose engine to release file locks before deleting
    await engine.dispose()
    
    if os.path.exists(db_path):
        backup = db_path + ".backup"
        shutil.copy2(db_path, backup)
        os.remove(db_path)
        print(f"  [OK] Old database backed up to {os.path.basename(backup)}")
    
    print("\n[*] Creating fresh database with current schema...")
    from app.database import init_db
    await init_db()
    print("  [OK] All tables created from current models")

    async with async_session() as session:
        try:
            # ── Foundation ──
            print("\n[*] Setting up foundation data...")
            church = await get_or_create_church(session)
            admin = await get_or_create_admin_user(session, church.id)
            funds = await create_funds(session, church.id)
            service = await create_service(session, church.id)
            vol_roles = await create_volunteer_roles(session, church.id)

            # ── Profile 1: Marcus Sterling ──
            await seed_marcus_sterling(session, church.id, admin.id, funds, service, vol_roles)

            # ── Profile 2: Chloe Vance ──
            await seed_chloe_vance(session, church.id, admin.id, service)

            # ── Profile 3: Julian Hayes ──
            await seed_julian_hayes(session, church.id, admin.id, service)

            # ── Profile 4: Evelyn Cho ──
            await seed_evelyn_cho(session, church.id, admin.id, funds, service)

            # ── Profile 5: The Miller Family ──
            await seed_miller_family(session, church.id, admin.id, service, vol_roles)

            # ── Historical data for charts ──
            await seed_historical_donations(session, church.id, funds)

            # ── Commit everything ──
            await session.commit()

            # ── Summary ──
            print("\n" + "=" * 65)
            print("🎉 SEED COMPLETE — Summary")
            print("=" * 65)
            print(f"""
  Church:      {church.name} (id={church.id})
  Admin User:  {admin.full_name} ({admin.email})
  
  👤 Members Seeded:
     1. Marcus Sterling  — 🟢 95 (Engaged Leader, Bass Guitar, $500/mo tithe)
     2. Chloe Vance      — 🔴 18 (At-Risk, missed 4 weeks, auto-task created)
     3. Julian Hayes     — 🟡 45 (First-time guest, URGENT care case)
     4. Evelyn Cho       — 🟡 60 (Big donor, $15K Building Fund, low attendance)
     5. Sam Miller       — 🟢 82 (Family head, weekly attender)
     6. Jessica Miller   — 🟢 78 (Pending nursery volunteer application)
     7. Leo Miller (4)   — Child, Pre-K check-in
     8. Maya Miller (2)  — Child, Nursery check-in

  📊 Dashboard Impact:
     • KPI Cards:      Members, Giving (MTD), Attendance, Groups, Care, Volunteers, Prayers — all populated
     • Giving Chart:   12 months of historical data + $15K spike from Evelyn
     • Attendance:     ~30+ records across profiles
     • Care Board:     1 URGENT / NEW case (Julian)
     • Volunteer Board: 1 pending application (Jessica), 12 hours logged (Marcus)
     • Absentee List:  Chloe Vance (4 weeks missed)
     • First-Time:     Julian Hayes (last Sunday)
     • Family View:    Miller Family (4 members, 2 child check-ins)
     • Prayer Board:   1 urgent prayer request
     • Funds:          General ($3,800+), Building ($15,000+)
     • Pledges:        1 active ($25K campaign, 60% fulfilled)

  🔑 Login:
     Email:    admin@newbirthfellowship.org
     Password: Admin123!
""")

        except Exception as e:
            await session.rollback()
            print(f"\n❌ SEED FAILED: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    asyncio.run(main())
