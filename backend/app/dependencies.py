import time
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, AuthSession
from app.security import verify_access_token
from app.config import public_key

auth_scheme = HTTPBearer(auto_error=False)

class Principal:
    def __init__(self, user: User, session: AuthSession):
        self.user = user
        self.session = session

def require_user(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
    db: Session = Depends(get_db)
) -> Principal:
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Sign in again to continue.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    try:
        claims = verify_access_token(token, public_key)
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Sign in again to continue.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_id = claims.get("sub")
    session_id = claims.get("sid")
    exp = claims.get("exp")

    # DB might be unavailable
    try:
        session = db.query(AuthSession).filter(AuthSession.id == session_id).first()
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")

    if not session:
        raise HTTPException(status_code=401, detail="Sign in again to continue.", headers={"WWW-Authenticate": "Bearer"})
    
    now = int(time.time())
    if session.revoked_at is not None or session.expires_at <= now or session.expires_at != exp:
        raise HTTPException(status_code=401, detail="Sign in again to continue.", headers={"WWW-Authenticate": "Bearer"})

    if session.user_id != user_id:
        raise HTTPException(status_code=401, detail="Sign in again to continue.", headers={"WWW-Authenticate": "Bearer"})

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Sign in again to continue.", headers={"WWW-Authenticate": "Bearer"})

    return Principal(user, session)
