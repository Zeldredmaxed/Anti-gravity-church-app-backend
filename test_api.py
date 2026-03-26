import asyncio
import httpx
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.church import Church
from app.models.user import User
from app.routers.auth import create_access_token, get_password_hash
from datetime import timedelta

async def setup_test_data():
    db = SessionLocal()
    
    # Clean up old test data if exists
    church = db.query(Church).filter(Church.subdomain == "test-live").first()
    if not church:
        church = Church(name="Test Live Church", subdomain="test-live")
        db.add(church)
        db.commit()
        db.refresh(church)
        
    user = db.query(User).filter(User.email == "live@test.com").first()
    if not user:
        user = User(
            email="live@test.com",
            hashed_password=get_password_hash("password123"),
            full_name="Live Tester",
            church_id=church.id,
            role="admin"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
    token = create_access_token(
        data={"sub": user.email, "church_id": church.id, "role": user.role},
        expires_delta=timedelta(minutes=30)
    )
    
    db.close()
    return token

async def main():
    token = await setup_test_data()
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000/api/v1", headers=headers) as client:
        print("\n1. Testing Bible Endpoint...")
        res = await client.get("/bible/John/3/16")
        print(f"Status: {res.status_code}, Response: {res.text[:100]}")
        
        print("\n2. Testing Sermons Creation...")
        sermon_data = {
            "title": "Sunday Live",
            "video_url": "https://youtube.com/watch?v=123",
            "video_type": "youtube",
            "is_published": True
        }
        res = await client.post("/sermons", json=sermon_data)
        print(f"Status: {res.status_code}, Response: {res.text[:100]}")
        sermon_id = res.json().get("id")
        
        if sermon_id:
            print(f"\n3. Testing Sermon Note Creation...")
            note_data = {
                "content": "Great point here!",
                "timestamp_marker": 120
            }
            res = await client.post(f"/sermons/{sermon_id}/notes", json=note_data)
            print(f"Status: {res.status_code}, Response: {res.text[:100]}")

        print("\n4. Testing Active Scripture...")
        scripture_data = {
            "title": "Opening Verse",
            "book": "John",
            "chapter": 3,
            "verse_start": 16,
            "verse_end": 17,
            "pastor_notes": "God's love.",
            "is_active": True
        }
        res = await client.post("/scriptures", json=scripture_data)
        print(f"Status: {res.status_code}, Response: {res.text[:100]}")
        
        res = await client.get("/scriptures/active")
        print(f"Status: {res.status_code}, Active Scripture Response: {res.text[:200]}")

if __name__ == "__main__":
    asyncio.run(main())
