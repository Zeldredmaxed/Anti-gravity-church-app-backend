import asyncio
from sqlalchemy import select, update
from app.database import engine, Base, init_db, async_session
from app.models import __init__ as _models
from app.models.church import Church
from app.models.campus import Campus
from app.models.member import Member
from app.models.event import Event
from app.models.group import Group
from app.models.attendance import Service

async def backfill():
    async with async_session() as db:
        print("Fetching churches...")
        churches = (await db.execute(select(Church))).scalars().all()
        
        for church in churches:
            print(f"Processing church {church.id}: {church.name}")
            
            # Check if a campus already exists
            campus = (await db.execute(
                select(Campus).where(Campus.church_id == church.id, Campus.name == "Main Campus")
            )).scalar_one_or_none()
            
            if not campus:
                print("  Creating 'Main Campus'...")
                campus = Campus(
                    church_id=church.id,
                    name="Main Campus",
                    is_main_campus=True,
                    address=church.address
                )
                db.add(campus)
                await db.flush()
                print(f"  Created campus ID: {campus.id}")
            
            campus_id = campus.id
            
            # Update Member
            print("  Backfilling Members...")
            res = await db.execute(
                update(Member)
                .where(Member.church_id == church.id, Member.campus_id == None)
                .values(campus_id=campus_id)
            )
            print(f"    Updated {res.rowcount} members")
            
            # Update Event
            print("  Backfilling Events...")
            res = await db.execute(
                update(Event)
                .where(Event.church_id == church.id, Event.campus_id == None)
                .values(campus_id=campus_id)
            )
            print(f"    Updated {res.rowcount} events")
            
            # Update Group
            print("  Backfilling Groups...")
            res = await db.execute(
                update(Group)
                .where(Group.church_id == church.id, Group.campus_id == None)
                .values(campus_id=campus_id)
            )
            print(f"    Updated {res.rowcount} groups")
            
            # Update Service
            print("  Backfilling Services...")
            res = await db.execute(
                update(Service)
                .where(Service.church_id == church.id, Service.campus_id == None)
                .values(campus_id=campus_id)
            )
            print(f"    Updated {res.rowcount} services")
            
        await db.commit()
        print("Done backfilling for all churches.")

if __name__ == "__main__":
    asyncio.run(backfill())
