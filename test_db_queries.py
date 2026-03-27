import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, text
from app.config import settings
from app.models.glory_clip import GloryClip
import app.models.user
import app.models.church

async def test_queries():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        print("Testing /shorts/me query...")
        try:
            query = select(GloryClip).where(GloryClip.author_id == 1, GloryClip.is_deleted == False)
            await session.execute(query)
            print("OK")
        except Exception as e:
            print("FAILED:", e)

        print("\nTesting /shorts/trending query...")
        try:
            query = select(GloryClip).where(GloryClip.is_deleted == False, GloryClip.moderation_status == "approved")
            await session.execute(query)
            print("OK")
        except Exception as e:
            print("FAILED:", e)

        print("\nTesting simple attributes...")
        try:
            res = await session.execute(select(GloryClip).limit(1))
            clip = res.scalar_one_or_none()
            if clip:
                print(clip.share_count)
            print("OK")
        except Exception as e:
            print("FAILED:", e)

if __name__ == "__main__":
    asyncio.run(test_queries())
