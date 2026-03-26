import asyncio
from sqlalchemy import text
from app.database import engine

async def run_migrations():
    async with engine.begin() as conn:
        migrations = [
            "ALTER TABLE users ALTER COLUMN church_id DROP NOT NULL;",
            "ALTER TABLE users ADD COLUMN username VARCHAR(50);",
            "ALTER TABLE users ADD COLUMN date_of_birth TIMESTAMP WITH TIME ZONE;",
            "ALTER TABLE users ADD COLUMN stripe_customer_id VARCHAR(255);",
            "ALTER TABLE users ADD COLUMN testimony_summary TEXT;",
            "ALTER TABLE users RENAME COLUMN bio TO testimony_summary;",
            "ALTER TABLE users ADD COLUMN is_anointed BOOLEAN DEFAULT FALSE;",
            "ALTER TABLE users ADD COLUMN website VARCHAR(255);",
            "ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500);"
        ]
        
        for query in migrations:
            try:
                await conn.execute(text(query))
                print(f"Success: {query}")
            except Exception as e:
                # We expect "column already exists" or "column does not exist" errors
                print(f"Skipped: {query.split('ADD COLUMN')[-1][:15]}...")

if __name__ == "__main__":
    asyncio.run(run_migrations())
