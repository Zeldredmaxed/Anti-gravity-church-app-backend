import requests

def run():
    # Login as pastor
    login_res = requests.post("http://localhost:8080/api/v1/auth/login", json={"email": "pastor@newbirth.com", "password": "password123"})
    if login_res.status_code != 200:
        print("Login failed:", login_res.text)
        return
        
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test GET shorts
    res1 = requests.get("http://localhost:8080/api/v1/shorts/me", headers=headers)
    print("GET Shorts Result:", res1.status_code, res1.text[:200])
    
    # Test POST short
    payload = {
        "title": "Test Short",
        "video_url": "https://res.cloudinary.com/demo/video/upload/v123/file.mp4",
        "category": "worship"
    }
    res2 = requests.post("http://localhost:8080/api/v1/shorts", json=payload, headers=headers)
    print("POST Shorts Result:", res2.status_code, res2.text[:200])

if __name__ == "__main__":
    run()
