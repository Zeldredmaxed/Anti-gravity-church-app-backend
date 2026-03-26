import asyncio
import secrets
import string
import argparse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session_maker
from app.models.church import RegistrationKey

def generate_key_string() -> str:
    """Generate a clean, readable, secure key (e.g., NG-A4BX-99PL)"""
    chars = string.ascii_uppercase + string.digits
    part1 = ''.join(secrets.choice(chars) for _ in range(4))
    part2 = ''.join(secrets.choice(chars) for _ in range(4))
    return f"NG-{part1}-{part2}"

async def main():
    parser = argparse.ArgumentParser(description="Generate SaaS Registration Keys")
    parser.add_argument("--count", type=int, default=1, help="Number of keys to generate")
    args = parser.parse_args()

    async with async_session_maker() as session:
        keys = []
        for _ in range(args.count):
            key = RegistrationKey(key_string=generate_key_string())
            session.add(key)
            keys.append(key.key_string)
        
        await session.commit()
        
        print("\n" + "="*40)
        print(f"✅ Generated {args.count} Registration Key(s):")
        for k in keys:
            print(f"   {k}")
        print("="*40 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
