import asyncio
from sqlalchemy import text
from app.database import engine

async def run_migrations():
    async with engine.begin() as conn:
        migrations = [
            # Member updates
            "ALTER TABLE members ADD COLUMN salvation_status VARCHAR(50);",
            "ALTER TABLE members ADD COLUMN completed_membership_class BOOLEAN DEFAULT 0;",
            "ALTER TABLE members ADD COLUMN membership_class_date DATE;",
            "ALTER TABLE members ADD COLUMN health_score INTEGER;",
            "ALTER TABLE members ADD COLUMN health_status VARCHAR(20);",
            
            # Prayer request updates
            "ALTER TABLE prayer_requests ADD COLUMN assigned_leader_id INTEGER REFERENCES users(id);",
            "ALTER TABLE prayer_requests ADD COLUMN follow_up_log JSON;",
            
            # Sermon updates
            "ALTER TABLE sermons ADD COLUMN worship_setlist JSON;",
            "ALTER TABLE sermons ADD COLUMN volunteer_schedule_id INTEGER REFERENCES volunteer_schedules(id);",
            
            # Multi-Campus updates
            "ALTER TABLE members ADD COLUMN campus_id INTEGER REFERENCES campuses(id);",
            "ALTER TABLE events ADD COLUMN campus_id INTEGER REFERENCES campuses(id);",
            "ALTER TABLE groups ADD COLUMN campus_id INTEGER REFERENCES campuses(id);",
            "ALTER TABLE services ADD COLUMN campus_id INTEGER REFERENCES campuses(id);"
        ]
        
        for query in migrations:
            try:
                await conn.execute(text(query))
                print(f"Success: {query}")
            except Exception as e:
                # We expect "column already exists" or "column does not exist" errors
                print(f"Skipped: {query.split('ADD COLUMN')[-1][:25]}... (Reason: column likely exists)")

        # Create any new tables (checkin_sessions, volunteer_roles, assets, etc)
        from app.database import Base
        print("Running Base.metadata.create_all() for new tables...")
        # Since we use async engine, we need to use run_sync
        await conn.run_sync(Base.metadata.create_all)
        print("Done creating any new tables.")


if __name__ == "__main__":
    asyncio.run(run_migrations())
