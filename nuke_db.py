import asyncio
from app.database import engine, Base
import traceback

import app.main

async def nuke_and_rebuild():
    try:
        print("Dropping all tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            print("Dropped all tables. Rebuilding tables...")
            await conn.run_sync(Base.metadata.create_all)
        print("Database rebuilt successfully.")
    except Exception as e:
        with open("err.log", "w") as f:
            traceback.print_exc(file=f)
        print("Error written to err.log")

if __name__ == "__main__":
    asyncio.run(nuke_and_rebuild())
