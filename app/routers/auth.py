import os
import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.core.security import create_access_token
from app.core.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET

router = APIRouter(prefix="/users/auth", tags=["Google Authentication"])

@router.get("/google/login")
def google_login(request: Request):
    """
    Step 1: Send the user to Google's secure login screen.
    Uses incoming request context to build a foolproof redirect URI.
    """
    # Dynamically read the current host domain name (localhost or render URL)
    base_url = str(request.base_url).rstrip("/")
    dynamic_redirect_uri = f"{base_url}/users/auth/google/callback"
    
    google_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={dynamic_redirect_uri}&"
        f"response_type=code&"
        f"scope=openid%20profile%20email"
    )
    return RedirectResponse(url=google_url)


@router.get("/google/callback")
async def google_callback(code: str, request: Request, db: Session = Depends(get_db)):
    """
    Step 2: Google redirects the user back here with a temporary code.
    We trade that code for their real, verified email profile details.
    """
    # Re-calculate the exact same redirect URI so Google validates the match perfectly
    base_url = str(request.base_url).rstrip("/")
    dynamic_redirect_uri = f"{base_url}/users/auth/google/callback"

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": dynamic_redirect_uri,
        "grant_type": "authorization_code",
    }
    
    async with httpx.AsyncClient() as client:
        # Trade temporary code for a Google token
        token_res = await client.post(token_url, data=data)
        if token_res.status_code != 200:
            print(f"GOOGLE TOKEN EXCHANGE FAILED: {token_res.text}")
            raise HTTPException(status_code=400, detail="Failed to get token from Google")
        
        google_tokens = token_res.json()
        access_token = google_tokens.get("access_token")
        
        # Use token to grab profile data (name, email, avatar)
        user_info_res = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if user_info_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch user info from Google")
            
        user_info = user_info_res.json()

    email = user_info.get("email")
    name = user_info.get("name")
    avatar_url = user_info.get("picture")

    if not email:
        raise HTTPException(status_code=400, detail="Google account lacks email verification profile properties")

    # Look up the user in your database
    user = db.query(User).filter(User.email == email).first()

    # If they are a first-time user, register them automatically!
    if not user:
        try:
            user = User(
                name=name,
                email=email,
                avatar_url=avatar_url,
                hashed_password="OAUTH_GOOGLE_ACCOUNT_PROFILES",
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        except Exception as e:
            db.rollback()
            print(f"DATABASE INSERTION ERROR: {e}")
            raise HTTPException(status_code=500, detail="Failed to save new Google user to database records")

    # Step 3: Issue our OWN internal JWT token using their true row ID
    internal_token = create_access_token(data={"sub": str(user.id)})

    # Dynamic Redirection routing logic based on your production environment
    frontend_base_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
    frontend_success_url = f"{frontend_base_url}/login-success?token={internal_token}"
    
    return RedirectResponse(url=frontend_success_url)