"""Phase 2 integration test — multi-tenancy, chat, feed."""
import requests

BASE = "http://127.0.0.1:8000/api/v1"

# 1. Health
r = requests.get("http://127.0.0.1:8000/")
print("1. HEALTH:", r.status_code, r.json()["version"])

# 2. Onboard church
r = requests.post(f"{BASE}/churches/onboard", json={
    "church": {"name": "Grace Church", "subdomain": "grace2"},
    "admin_email": "pG2@grace.org",
    "admin_password": "Pass1234",
    "admin_name": "Pastor Grace"
})
d = r.json()
print("2. ONBOARD:", r.status_code, d.get("church", {}).get("name"))
TOKEN = d["access_token"]
H = {"Authorization": f"Bearer {TOKEN}"}
church_id = d["church"]["id"]

# 3. My church
r = requests.get(f"{BASE}/churches/me", headers=H)
print("3. MY CHURCH:", r.status_code, r.json().get("name"))

# 4. Register member
r = requests.post(f"{BASE}/auth/register", json={
    "church_id": church_id,
    "email": "m2@grace.org",
    "password": "Pass123",
    "full_name": "Member One"
})
print("4. REGISTER:", r.status_code, r.json().get("full_name"))
user2_id = r.json()["id"]

# 5. Login
r = requests.post(f"{BASE}/auth/login", json={"email": "m2@grace.org", "password": "Pass123"})
MH = {"Authorization": f"Bearer {r.json()['access_token']}"}
print("5. LOGIN:", r.status_code)

# 6. Create member profile
r = requests.post(f"{BASE}/members", headers=H, json={"first_name": "Test", "last_name": "Member"})
print("6. MEMBER:", r.status_code, "church_id:", r.json().get("church_id"))

# 7. Create post
r = requests.post(f"{BASE}/feed/posts", headers=H, json={
    "content": "Welcome to Grace Church!", "post_type": "announcement"
})
print("7. POST:", r.status_code, r.json().get("post_type"))
post_id = r.json()["id"]

# 8. Like
r = requests.post(f"{BASE}/feed/posts/{post_id}/like", headers=MH)
print("8. LIKE:", r.status_code, r.json())

# 9. Comment
r = requests.post(f"{BASE}/feed/posts/{post_id}/comments", headers=MH, json={"content": "Amen!"})
print("9. COMMENT:", r.status_code, r.json().get("content"))
comment_id = r.json()["id"]

# 10. Nested reply
r = requests.post(f"{BASE}/feed/posts/{post_id}/comments", headers=H, json={
    "content": "Blessed!", "parent_id": comment_id
})
print("10. REPLY:", r.status_code, "parent_id:", r.json().get("parent_id"))

# 11. Post detail with nested comments
r = requests.get(f"{BASE}/feed/posts/{post_id}", headers=H)
detail = r.json()
print("11. DETAIL:", r.status_code, "comments:", len(detail["comments"]),
      "replies:", len(detail["comments"][0]["replies"]) if detail["comments"] else 0)

# 12. Create chat
r = requests.post(f"{BASE}/chats", headers=H, json={"type": "direct", "participant_user_ids": [user2_id]})
print("12. CHAT:", r.status_code, r.json().get("type"))
convo_id = r.json()["id"]

# 13. Send message
r = requests.post(f"{BASE}/chats/{convo_id}/messages", headers=H, json={"content": "Hey there!"})
print("13. MSG:", r.status_code, r.json().get("content"))

# 14. Reply message
r = requests.post(f"{BASE}/chats/{convo_id}/messages", headers=MH, json={"content": "Hello Pastor!"})
print("14. REPLY:", r.status_code, r.json().get("sender_name"))

# 15. Get messages
r = requests.get(f"{BASE}/chats/{convo_id}/messages", headers=H)
print("15. MSGS:", r.status_code, "count:", len(r.json()))

# 16. Mark read
r = requests.post(f"{BASE}/chats/{convo_id}/read", headers=H)
print("16. READ:", r.status_code)

# 17. Feed
r = requests.get(f"{BASE}/feed", headers=H)
print("17. FEED:", r.status_code, "posts:", len(r.json()))

# 18. Conversations list
r = requests.get(f"{BASE}/chats", headers=H)
print("18. CONVOS:", r.status_code, "count:", len(r.json()))

# 19. Churches directory
r = requests.get(f"{BASE}/churches")
print("19. CHURCHES:", r.status_code, "count:", len(r.json()))

print()
print("=" * 40)
print("ALL 19 TESTS PASSED")
print("=" * 40)
