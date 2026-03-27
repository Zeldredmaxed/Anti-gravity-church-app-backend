import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, text
from app.config import settings
from app.models.glory_clip import GloryClip
import app.models.user
import app.models.church


async def check_shorts():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        # Count shorts
        result = await session.execute(select(GloryClip))
        clips = result.scalars().all()
        print(f"Total shorts found: {len(clips)}")
        for clip in clips:
            print(f"- ID: {clip.id}, Title: {clip.title[:50]}, Author ID: {clip.author_id}, Deleted: {clip.is_deleted}, Video: {clip.video_url[:50]}")

if __name__ == "__main__":
    asyncio.run(check_shorts())
