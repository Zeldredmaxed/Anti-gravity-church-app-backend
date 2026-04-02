import asyncio
import app.main
import traceback

async def run():
    try:
        await app.main.nuke_database_dangerous()
        await app.main.seed_church_dangerous()
        res = await app.main.seed_dummy_data_dangerous()
        print("SEED DUMMY RESULTS:")
        print(res)
    except Exception as e:
        print("REAL EXCEPTION:")
        traceback.print_exc()

import pprint
import _io
def get_it():
    import asyncio, app.main
    async def run():
        await app.main.nuke_database_dangerous()
        await app.main.seed_church_dangerous()
        res = await app.main.seed_dummy_data_dangerous()
        with open("clean_error.txt", "w") as f:
            pprint.pprint(res, stream=f)
    asyncio.run(run())

get_it()
