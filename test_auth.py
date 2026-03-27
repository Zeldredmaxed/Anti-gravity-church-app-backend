import sys
try:
    from app.routers.auth import _track_login, get_my_streak
    from app.main import app
    print("Imports successful!")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
