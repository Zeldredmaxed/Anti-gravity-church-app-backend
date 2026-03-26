# New Birth Church Management System

A production-ready, white-label church management backend built with **FastAPI** + **SQLAlchemy** + **PostgreSQL/SQLite**.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start development server
uvicorn app.main:app --reload --port 8000

# Open API docs
# http://localhost:8000/docs
```

## API Endpoints

All endpoints are under `/api/v1/`:

| Module | Prefix | Key Features |
|--------|--------|-------------|
| **Auth** | `/auth` | Register, login, JWT refresh, profile |
| **Members** | `/members` | CRM profiles, baptism tracking, notes, CSV import/export, engagement scoring |
| **Families** | `/families` | Household management, relationship types |
| **Funds** | `/funds` | Fund accounting, budgets, expenses, restricted fund controls |
| **Donations** | `/donations` | Recording, batch entry, donor summaries, IRS-compliant PDF statements |
| **Pledges** | `/pledges` | Campaign pledges with progress tracking |
| **Attendance** | `/attendance` | Check-in/out, service management, trends, absentee alerts, first-time guests |
| **Groups** | `/groups` | Small groups, ministry teams, capacity management |
| **Reports** | `/reports` | Dashboard, giving/attendance analytics, financial reports, CSV export |
| **Admin** | `/admin` | User management, role updates, audit logs, church settings |

## User Roles (RBAC)

- `admin` — Full access to everything
- `pastor` — Member data, giving, attendance, pastoral notes
- `staff` — Standard operational access
- `volunteer` — Limited access
- `member` — Self-service access

## Environment Variables

Copy `.env.example` to `.env` and configure:

```
DATABASE_URL=sqlite+aiosqlite:///./newbirth_church.db  # Dev
DATABASE_URL=postgresql+asyncpg://user:pass@host/db    # Production
SECRET_KEY=your-production-secret-key
CHURCH_NAME=Your Church Name
```

## Architecture

```
app/
├── main.py           # FastAPI app + router registration
├── config.py         # Environment-based settings
├── database.py       # Async SQLAlchemy engine
├── models/           # ORM models (16 tables)
├── schemas/          # Pydantic request/response validation
├── routers/          # API route handlers
├── middleware/        # Audit trail
└── utils/            # JWT, passwords, CSV, PDF
```
