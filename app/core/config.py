import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

SECRET_KEY = os.getenv("SECRET_KEY", "flowboard_super_secret_key_change_in_production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# 🌟 Google OAuth Credentials
# It will read from your environment variables first, falling back to your keys during local testing
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "PASTE_YOUR_ACTUAL_CLIENT_ID_HERE.apps.googleusercontent.com")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "PASTE_YOUR_ACTUAL_CLIENT_SECRET_HERE")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/users/auth/google/callback")