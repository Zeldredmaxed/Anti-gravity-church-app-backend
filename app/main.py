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
from app.routers.glory_clips import router as glory_clips_router
from app.routers.events import router as events_router
from app.routers.prayers import router as prayers_router
from app.routers.alerts import router as alerts_router, notifications_router
from app.routers.sermons import router as sermons_router
from app.routers.bible import router as bible_router
from app.routers.scriptures import router as scriptures_router
from app.routers.social import router as social_router
from app.routers.seek import router as seek_router
from app.routers.store import router as store_router
from app.routers.shorts import router as shorts_router
from app.routers.chat import router as chat_router
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
    migrations = [
        # ── Users table ──
        "ALTER TABLE users ALTER COLUMN church_id DROP NOT NULL;",
        "ALTER TABLE users ADD COLUMN username VARCHAR(50);",
        "ALTER TABLE users ADD COLUMN date_of_birth TIMESTAMP WITH TIME ZONE;",
        "ALTER TABLE users ADD COLUMN stripe_customer_id VARCHAR(255);",
        "ALTER TABLE users ADD COLUMN testimony_summary TEXT;",
        "ALTER TABLE users RENAME COLUMN bio TO testimony_summary;",
        "ALTER TABLE users ADD COLUMN is_anointed BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE users ADD COLUMN website VARCHAR(255);",
        "ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500);",
        # ── Churches table ──
        "ALTER TABLE churches ADD COLUMN description TEXT;",
        "ALTER TABLE churches ADD COLUMN logo_url VARCHAR(500);",
        "ALTER TABLE churches ADD COLUMN address VARCHAR(500);",
        "ALTER TABLE churches ADD COLUMN phone VARCHAR(20);",
        "ALTER TABLE churches ADD COLUMN email VARCHAR(255);",
        "ALTER TABLE churches ADD COLUMN website VARCHAR(255);",
        "ALTER TABLE churches ADD COLUMN pastor_name VARCHAR(255);",
        "ALTER TABLE churches ADD COLUMN youtube_channel_id VARCHAR(50);",
        "ALTER TABLE churches ADD COLUMN latitude FLOAT;",
        "ALTER TABLE churches ADD COLUMN longitude FLOAT;",
        "ALTER TABLE churches ADD COLUMN settings JSON;",
        # ── Sermons table ──
        "ALTER TABLE sermons ADD COLUMN transcript TEXT;",
        # ── GloryClips table ──
        "ALTER TABLE glory_clips ADD COLUMN thumbnail_url VARCHAR(500);",
        "ALTER TABLE glory_clips ADD COLUMN duration_seconds INTEGER;",
        "ALTER TABLE glory_clips ADD COLUMN view_count INTEGER DEFAULT 0;",
        "ALTER TABLE glory_clips ADD COLUMN amen_count INTEGER DEFAULT 0;",
        "ALTER TABLE glory_clips ADD COLUMN comment_count INTEGER DEFAULT 0;",
        "ALTER TABLE glory_clips ADD COLUMN share_count INTEGER DEFAULT 0;",
        "ALTER TABLE glory_clips ADD COLUMN is_featured BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE glory_clips ADD COLUMN tags JSON;",
        "ALTER TABLE glory_clips ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE;",
        # ── Posts table (feed) ──
        "ALTER TABLE posts ADD COLUMN amen_count INTEGER DEFAULT 0;",
        "ALTER TABLE posts ADD COLUMN comments_count INTEGER DEFAULT 0;",
        "ALTER TABLE posts ADD COLUMN shares_count INTEGER DEFAULT 0;",
        "ALTER TABLE posts ADD COLUMN is_pinned BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE posts ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE posts ADD COLUMN media_urls JSON;",
        "ALTER TABLE posts ADD COLUMN post_type VARCHAR(30) DEFAULT 'text';",
        "ALTER TABLE posts ADD COLUMN visibility VARCHAR(20) DEFAULT 'members_only';",
    ]
    
    for query in migrations:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(query))
        except Exception as e:
            print(f"Migration skipped/failed for '{query[:30]}...': {e}")
            pass # Ignore if column already exists or bio doesn't exist
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
        "shorts, events, prayer requests, notifications, and analytics. "
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
app.include_router(glory_clips_router, prefix=API_PREFIX)
app.include_router(events_router, prefix=API_PREFIX)
app.include_router(prayers_router, prefix=API_PREFIX)
app.include_router(alerts_router, prefix=API_PREFIX)
app.include_router(sermons_router, prefix=API_PREFIX)
app.include_router(bible_router, prefix=API_PREFIX)
app.include_router(scriptures_router, prefix=API_PREFIX)
app.include_router(shorts_router, prefix=API_PREFIX)
app.include_router(chat_router, prefix=API_PREFIX)
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
from app.routers.assistant import router as assistant_router

# WebSocket (no API prefix — mounted at /ws/chat/{id})
app.include_router(ws_router)
app.include_router(assistant_router, prefix=API_PREFIX)


@app.get("/", tags=["Health"])
async def root():
    return {
        "name": settings.CHURCH_NAME,
        "service": "Church Management System",
        "version": "3.0.0",
        "status": "operational",
        "features": [
            "multi-tenant", "chat", "feed", "shorts", "events",
            "prayers", "notifications", "crm", "giving", "attendance",
        ],
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}
