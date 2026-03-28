import asyncio
from app.main import app

async def main():
    try:
        async with app.router.lifespan_context(app):
            print("LIFESPAN OK")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
