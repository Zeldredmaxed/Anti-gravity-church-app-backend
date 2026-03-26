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
from app.routers.alerts import router as alerts_router
from app.routers.sermons import router as sermons_router
from app.routers.bible import router as bible_router
from app.routers.scriptures import router as scriptures_router
from app.routers.social import router as social_router
from app.routers.seek import router as seek_router
from app.routers.store import router as store_router


from sqlalchemy import text
from app.database import engine
import app.models.store  # Ensure Base metadata collects the Product model during migration

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()
    
    # Run critical one-time migration for church_id 
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE users ALTER COLUMN church_id DROP NOT NULL;"))
            print("Successfully made users.church_id nullable.")
            
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(50);"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS date_of_birth TIMESTAMP WITH TIME ZONE;"))
            print("Successfully ensured username and date_of_birth columns exist.")
        except Exception as e:
            print(f"Migration logged: {e}")

    yield


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

# WebSocket (no API prefix — mounted at /ws/chat/{id})
app.include_router(ws_router)


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
