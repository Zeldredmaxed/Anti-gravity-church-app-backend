import asyncio
from app.database import engine, Base
import app.models  # Ensures all models are imported

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(main())
