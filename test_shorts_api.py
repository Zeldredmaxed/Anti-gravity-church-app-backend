import requests

def run():
    base = "https://anti-gravity-church-app-backend-production.up.railway.app/api/v1"
    
    # 1. Register a test user
    reg = requests.post(f"{base}/auth/register", json={
        "email": "testagent@newbirth.com",
        "username": "testagent123",
        "password": "password123",
        "full_name": "Test Agent",
        "role": "user"
    })
    
    # It might already exist, so just login anyway
    login_res = requests.post(f"{base}/auth/login", json={"email": "testagent@newbirth.com", "password": "password123"})
    
    if login_res.status_code != 200:
        print("Login failed:", login_res.text)
        return
        
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    import json
    # Test GET shorts debug
    res1 = requests.get(f"{base}/shorts/debug", headers=headers)
    
    with open("results.json", "w", encoding="utf-8") as f:
        try:
            f.write(json.dumps(res1.json(), indent=2))
        except:
            f.write(res1.text)
    
    print("GET shorts debug status:", res1.status_code)
    
    # Test GET glory clips trending
    res2 = requests.get(f"{base}/glory_clips/trending", headers=headers)
    print("GET glory_clips trending status:", res2.status_code)
    if res2.status_code != 200:
        print("ERROR TEXT:", res2.text[:200])
    
    # Test GET shorts me
    res3 = requests.get(f"{base}/shorts/me", headers=headers)
    print("GET shorts me status:", res3.status_code)

if __name__ == "__main__":
    run()
