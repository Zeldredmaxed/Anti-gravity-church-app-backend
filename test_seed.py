import asyncio
import os
from app.main import nuke_database_dangerous, seed_church_dangerous, seed_dummy_data_dangerous

async def main():
    if os.path.exists("newbirth_church.db"):
        os.remove("newbirth_church.db")
    
    try:
        print("Nuking...")
        print(await nuke_database_dangerous())
        print("Seeding church...")
        print(await seed_church_dangerous())
        print("Seeding dummy...")
        print(await seed_dummy_data_dangerous())
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(e)

if __name__ == "__main__":
    asyncio.run(main())
