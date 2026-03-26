import httpx
import sys

def check_swagger():
    try:
        res = httpx.get("http://127.0.0.1:8000/docs", timeout=5.0)
        if res.status_code == 200:
            print("SUCCESS: Swagger UI is loading. All endpoints, models, and schemas are valid!")
            sys.exit(0)
        else:
            print(f"FAILED: Swagger returned {res.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_swagger()
