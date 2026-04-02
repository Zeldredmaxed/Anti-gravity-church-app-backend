"""New Birth Church Management System — FastAPI Application Entry Point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.middleware.audit import AuditMiddleware

# Import all routers
from app.routers.auth import router as auth_router
from app.routers.churches import router as churches_router
from app.routers.members import router as members_router
from app.routers.families import router as families_router
from app.routers.funds import router as funds_router
from app.routers.donations import router as donations_router, pledge_router
from app.routers.attendance import router as attendance_router
from app.routers.groups import router as groups_router
from app.routers.reports import router as reports_router
from app.routers.admin import router as admin_router
from app.routers.fellowship_chat import router as fellowship_chat_router
from app.routers.feed import router as feed_router
from app.routers.websocket import router as ws_router
from app.routers.clips import router as clips_router
from app.routers.events import router as events_router
from app.routers.prayers import router as prayers_router
from app.routers.alerts import router as alerts_router, notifications_router
from app.routers.sermons import router as sermons_router
from app.routers.bible import router as bible_router
from app.routers.scriptures import router as scriptures_router
from app.routers.social import router as social_router
from app.routers.seek import router as seek_router
from app.routers.store import router as store_router
from app.routers.payment_methods import router as payment_methods_router
from app.routers.support import router as support_router
from app.routers.uploads import router as uploads_router
from app.routers.music import router as music_router
from app.routers.automations import router as automations_router
from app.routers.assets import router as assets_router
from app.routers.checkin import router as checkin_router
from app.routers.communications import router as communications_router
from app.routers.campuses import router as campuses_router
from app.routers.discipleship import router as discipleship_router
from app.routers.tasks import router as tasks_router
from app.routers.volunteers import router as volunteers_router
from app.routers.care import router as care_router
from app.routers.dashboard import router as dashboard_router
from app.routers.two_factor import router as two_factor_router
from app.routers.activity import router as activity_router
from app.routers.facilities import router as facilities_router
from app.routers.statements import router as statements_router
from app.routers.stripe_webhooks import router as stripe_webhooks_router
from sqlalchemy import text
from app.database import engine
import app.models.store  # Ensure Base metadata collects the Product model during migration
import app.routers.payment_methods  # Ensure PaymentMethod model is collected
import app.routers.support  # Ensure SupportTicket model is collected
import app.models.music  # Ensure music models are collected

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()
    
    # Run critical one-time migrations
    migrations = []
    
    for query in migrations:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(query))
        except Exception as e:
            e_str = str(e).lower()
            # Ignore harmless expected errors for duplicate columns or non-existent sequences
            if "already exists" not in e_str and "does not exist" not in e_str:
                print(f"Migration skipped/failed for '{query[:30]}...': {e}")
    print("Completed automated schema checks.")

    # Start background tasks
    import asyncio
    from app.services.automation_runner import automation_task_runner
    runner_task = asyncio.create_task(automation_task_runner())

    yield
    
    # Cancel background tasks
    runner_task.cancel()


app = FastAPI(
    title=f"{settings.CHURCH_NAME} — Management System",
    description=(
        "Multi-tenant church management backend with member CRM, fund accounting, "
        "donation tracking, attendance, groups, real-time chat, social feed, "
        "glory clips, events, prayer requests, notifications, and analytics. "
        "White-label ready."
    ),
    version="3.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Audit trail middleware
app.add_middleware(AuditMiddleware)

# Register all routers under /api/v1 prefix
API_PREFIX = "/api/v1"
app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(churches_router, prefix=API_PREFIX)
app.include_router(members_router, prefix=API_PREFIX)
app.include_router(families_router, prefix=API_PREFIX)
app.include_router(funds_router, prefix=API_PREFIX)
app.include_router(donations_router, prefix=API_PREFIX)
app.include_router(social_router, prefix=API_PREFIX)
app.include_router(seek_router, prefix=API_PREFIX)
app.include_router(store_router, prefix=API_PREFIX)
app.include_router(pledge_router, prefix=API_PREFIX)
app.include_router(attendance_router, prefix=API_PREFIX)
app.include_router(groups_router, prefix=API_PREFIX)
app.include_router(reports_router, prefix=API_PREFIX)
app.include_router(admin_router, prefix=API_PREFIX)
app.include_router(fellowship_chat_router, prefix=API_PREFIX)
app.include_router(feed_router, prefix=API_PREFIX)
app.include_router(clips_router, prefix=API_PREFIX)
app.include_router(events_router, prefix=API_PREFIX)
app.include_router(prayers_router, prefix=API_PREFIX)
app.include_router(alerts_router, prefix=API_PREFIX)
app.include_router(sermons_router, prefix=API_PREFIX)
app.include_router(bible_router, prefix=API_PREFIX)
app.include_router(scriptures_router, prefix=API_PREFIX)
app.include_router(payment_methods_router, prefix=API_PREFIX)
app.include_router(support_router, prefix=API_PREFIX)
app.include_router(notifications_router, prefix=API_PREFIX)
app.include_router(uploads_router, prefix=API_PREFIX)
app.include_router(music_router, prefix=API_PREFIX)
app.include_router(automations_router, prefix=API_PREFIX)
app.include_router(assets_router, prefix=API_PREFIX)
app.include_router(checkin_router, prefix=API_PREFIX)
app.include_router(communications_router, prefix=API_PREFIX)
app.include_router(campuses_router, prefix=API_PREFIX)
app.include_router(discipleship_router, prefix=API_PREFIX)
app.include_router(tasks_router, prefix=API_PREFIX)
app.include_router(volunteers_router, prefix=API_PREFIX)
app.include_router(care_router, prefix=API_PREFIX)
app.include_router(dashboard_router, prefix=API_PREFIX)
app.include_router(two_factor_router, prefix=API_PREFIX)
app.include_router(activity_router, prefix=API_PREFIX)
app.include_router(facilities_router, prefix=API_PREFIX)
app.include_router(statements_router, prefix=API_PREFIX)
app.include_router(stripe_webhooks_router, prefix=API_PREFIX)
from app.routers.assistant import router as assistant_router

# WebSocket (no API prefix — mounted at /ws/chat/{id})
app.include_router(ws_router)
app.include_router(assistant_router, prefix=API_PREFIX)


@app.get("/nuke-database-dangerous")
async def nuke_database_dangerous():
    from app.database import engine, Base, db_url
    from sqlalchemy import text
    try:
        async with engine.begin() as conn:
            if "sqlite" in db_url:
                await conn.run_sync(Base.metadata.drop_all)
            else:
                await conn.execute(text("DROP SCHEMA public CASCADE;"))
                await conn.execute(text("CREATE SCHEMA public;"))
            await conn.run_sync(Base.metadata.create_all)
        return {"message": "Database completely wiped and rebuilt."}
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

@app.get("/", tags=["Health"])
async def root():
    return {
        "name": settings.CHURCH_NAME,
        "service": "Church Management System",
        "version": "4.0.0",
        "status": "operational",
        "features": [
            "multi-tenant", "chat", "feed", "glory_clips", "events",
            "prayers", "notifications", "crm", "giving", "attendance",
            "2fa", "facilities", "stripe", "sms", "email",
            "activity-timeline", "care-notes", "volunteer-hours",
            "dashboard-analytics", "giving-statements",
        ],
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}
