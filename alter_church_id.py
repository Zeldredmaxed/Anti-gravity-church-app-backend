import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def run():
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("No DATABASE_URL found.")
        return
    
    print(f"Connecting to DB...")
    conn = await asyncpg.connect(url)
    try:
        print("Making church_id nullable in users table...")
        await conn.execute("ALTER TABLE users ALTER COLUMN church_id DROP NOT NULL;")
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run())
