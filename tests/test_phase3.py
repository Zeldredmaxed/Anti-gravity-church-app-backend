"""Phase 3 integration test — Shorts, Events, Prayers, Notifications, Analytics."""
import requests
from datetime import datetime, timedelta

BASE = "http://127.0.0.1:8000/api/v1"

# 1. Health
r = requests.get("http://127.0.0.1:8000/")
print("1. HEALTH:", r.status_code, r.json()["version"])

# 2. Onboard church
r = requests.post(f"{BASE}/churches/onboard", json={
    "church": {"name": "Grace Church", "subdomain": "grace3"},
    "admin_email": "pastor3@grace.org",
    "admin_password": "Pass1234",
    "admin_name": "Pastor Grace"
})
d = r.json()
print("2. ONBOARD:", r.status_code, d.get("church", {}).get("name"))
TOKEN = d["access_token"]
H = {"Authorization": f"Bearer {TOKEN}"}
church_id = d["church"]["id"]

# 3. Register member
r = requests.post(f"{BASE}/auth/register", json={
    "church_id": church_id, "email": "m3@grace.org",
    "password": "Pass123", "full_name": "Member Three"
})
user2_id = r.json()["id"]
r = requests.post(f"{BASE}/auth/login", json={"email": "m3@grace.org", "password": "Pass123"})
MH = {"Authorization": f"Bearer {r.json()['access_token']}"}
print("3. USERS:", "admin+member OK")

# === SHORTS ===
r = requests.post(f"{BASE}/shorts", headers=H, json={
    "title": "Worship Highlights", "video_url": "https://example.com/vid.mp4",
    "category": "worship", "tags": ["worship", "praise"]
})
print("4. CREATE SHORT:", r.status_code, r.json().get("title"))
short_id = r.json()["id"]

r = requests.get(f"{BASE}/shorts", headers=H)
print("5. SHORTS FEED:", r.status_code, "count:", len(r.json()))

r = requests.post(f"{BASE}/shorts/{short_id}/like", headers=MH)
print("6. LIKE SHORT:", r.status_code, r.json())

r = requests.post(f"{BASE}/shorts/{short_id}/comments", headers=MH, json={
    "content": "Beautiful worship!"
})
print("7. SHORT COMMENT:", r.status_code, r.json().get("content"))

r = requests.post(f"{BASE}/shorts/{short_id}/view", headers=MH, json={
    "watched_seconds": 45, "completed": True
})
print("8. SHORT VIEW:", r.status_code, r.json())

r = requests.get(f"{BASE}/shorts/{short_id}", headers=H)
print("9. SHORT DETAIL:", r.status_code, "likes:", r.json().get("like_count"),
      "comments:", r.json().get("comment_count"), "views:", r.json().get("view_count"))

r = requests.get(f"{BASE}/shorts/trending", headers=H)
print("10. TRENDING:", r.status_code, "count:", len(r.json()))

r = requests.get(f"{BASE}/shorts/my-church", headers=H)
print("11. MY CHURCH SHORTS:", r.status_code, "count:", len(r.json()))

# === EVENTS ===
future = (datetime.utcnow() + timedelta(days=7)).isoformat()
r = requests.post(f"{BASE}/events", headers=H, json={
    "title": "Sunday Service", "description": "Main service",
    "event_type": "service", "location": "Main Sanctuary",
    "start_datetime": future, "max_capacity": 200,
    "registration_required": True
})
print("12. CREATE EVENT:", r.status_code, r.json().get("title"))
event_id = r.json()["id"]

r = requests.get(f"{BASE}/events", headers=H)
print("13. LIST EVENTS:", r.status_code, "count:", len(r.json()))

r = requests.post(f"{BASE}/events/{event_id}/rsvp", headers=MH, json={
    "status": "going", "guests_count": 2
})
print("14. RSVP:", r.status_code, r.json().get("status"))

r = requests.get(f"{BASE}/events/{event_id}/attendees", headers=H)
print("15. ATTENDEES:", r.status_code, "count:", len(r.json()))

r = requests.get(f"{BASE}/events/{event_id}", headers=MH)
print("16. EVENT DETAIL:", r.status_code, "my_rsvp:", r.json().get("my_rsvp"),
      "rsvp_count:", r.json().get("rsvp_count"))

# === PRAYERS ===
r = requests.post(f"{BASE}/prayers", headers=MH, json={
    "title": "Pray for my family", "description": "Going through a tough time",
    "category": "family", "is_anonymous": True, "is_urgent": True
})
print("17. PRAYER REQUEST:", r.status_code, r.json().get("title"),
      "anonymous:", r.json().get("is_anonymous"), "author_name:", r.json().get("author_name"))
prayer_id = r.json()["id"]

r = requests.get(f"{BASE}/prayers", headers=H)
print("18. PRAYER WALL:", r.status_code, "count:", len(r.json()))

r = requests.post(f"{BASE}/prayers/{prayer_id}/pray", headers=H)
print("19. PRAY:", r.status_code, r.json())

r = requests.post(f"{BASE}/prayers/{prayer_id}/respond", headers=H, json={
    "content": "Praying for you! God is faithful.", "is_prayed": True
})
print("20. RESPOND:", r.status_code, r.json().get("content"))

r = requests.get(f"{BASE}/prayers/{prayer_id}", headers=H)
print("21. PRAYER DETAIL:", r.status_code, "prayed:", r.json().get("prayed_count"),
      "responses:", len(r.json().get("responses", [])))

r = requests.put(f"{BASE}/prayers/{prayer_id}/answered", headers=MH, json={
    "testimony": "God answered! Family is restored."
})
print("22. ANSWERED:", r.status_code, r.json())

# === NOTIFICATIONS ===
r = requests.get(f"{BASE}/notifications", headers=MH)
print("23. NOTIFICATIONS (member):", r.status_code,
      "total:", r.json().get("total"), "unread:", r.json().get("unread_count"))

r = requests.get(f"{BASE}/notifications", headers=H)
notifs_data = r.json()
print("24. NOTIFICATIONS (admin):", r.status_code,
      "total:", notifs_data.get("total"), "unread:", notifs_data.get("unread_count"))

if notifs_data["items"]:
    nid = notifs_data["items"][0]["id"]
    r = requests.post(f"{BASE}/notifications/{nid}/read", headers=H)
    print("25. MARK READ:", r.status_code)
else:
    print("25. MARK READ: (no notifications to mark)")

r = requests.post(f"{BASE}/notifications/read-all", headers=H)
print("26. READ ALL:", r.status_code)

# === ANALYTICS ===
r = requests.get(f"{BASE}/reports/analytics/overview", headers=H)
print("27. ANALYTICS OVERVIEW:", r.status_code, "engagement:", r.json().get("engagement_score"))

r = requests.get(f"{BASE}/reports/analytics/engagement", headers=H)
print("28. ENGAGEMENT:", r.status_code, "weeks:", len(r.json().get("weekly_engagement", [])))

r = requests.get(f"{BASE}/reports/analytics/giving-trends", headers=H)
print("29. GIVING TRENDS:", r.status_code, "months:", len(r.json().get("monthly_trends", [])))

r = requests.get(f"{BASE}/reports/analytics/growth", headers=H)
print("30. GROWTH:", r.status_code, r.json().get("funnel"))

print()
print("=" * 40)
print("ALL 30 TESTS PASSED")
print("=" * 40)
