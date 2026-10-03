import time
from uuid import uuid4
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.schemas import UserCreate, TokenResponse, UserResponse
from app.models import User, AuthSession, AuditEvent
from app.security import hash_password, verify_password, issue_access_token
from app.config import private_key
from app.rate_limit import limiter
from app.dependencies import require_user, Principal

router = APIRouter()

@router.post("/register", status_code=201)
def register(request: Request, user_in: UserCreate, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "127.0.0.1"
    limiter.check_register_rate(ip)
    
    limiter.acquire_argon2()
    try:
        hashed = hash_password(user_in.password)
    finally:
        limiter.release_argon2()

    now = int(time.time())
    new_user = User(
        username=user_in.username.strip().lower(),
        password_hash=hashed,
        created_at=now
    )
    
    request_id = str(uuid4())
    db.add(new_user)
    
    try:
        db.flush()
        audit = AuditEvent(
            user_id=new_user.id,
            event="REGISTER_SUCCESS",
            outcome="SUCCESS",
            request_id=request_id,
            created_at=now
        )
        db.add(audit)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username taken")

    return {"id": new_user.id, "username": new_user.username}

@router.post("/login", response_model=TokenResponse)
def login(request: Request, user_in: UserCreate, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "127.0.0.1"
    username = user_in.username.strip().lower()
    
    limiter.check_login_rate(ip, username)
    
    user = db.query(User).filter(User.username == username).first()
    
    limiter.acquire_argon2()
    try:
        if user:
            valid = verify_password(user.password_hash, user_in.password)
        else:
            # Dummy verify to mitigate timing attacks
            # Uses a precomputed valid argon2 hash of empty string just to burn time
            verify_password("$argon2id$v=19$m=19456,t=2,p=1$c2FsdHNhbHRzYWx0c2E$4C3K0t5U6j9v+G1qD6lO+lZ2X1N3T7mH3c3u8H4w2jA", user_in.password)
            valid = False
    finally:
        limiter.release_argon2()

    if not valid:
        limiter.record_failed_login(username)
        # We need a request_id for the audit but we don't know the user if user doesn't exist
        user_id = user.id if user else None
        audit = AuditEvent(
            user_id=user_id,
            event="LOGIN_FAILED",
            outcome="FAILURE",
            request_id=str(uuid4()),
            created_at=int(time.time()),
            reason_code="INVALID_CREDENTIALS"
        )
        db.add(audit)
        db.commit()
        raise HTTPException(status_code=401, detail="Sign in again to continue.", headers={"WWW-Authenticate": "Bearer"})

    limiter.clear_failed_login(username)
    
    now = int(time.time())
    session = AuthSession(
        user_id=user.id,
        created_at=now,
        expires_at=now + 900 # TOKEN_TTL is 900
    )
    db.add(session)
    db.flush()

    try:
        token, expires_at = issue_access_token(user.id, session.id, private_key)
        
        session.expires_at = expires_at
        
        audit = AuditEvent(
            user_id=user.id,
            event="LOGIN_SUCCESS",
            outcome="SUCCESS",
            request_id=str(uuid4()),
            created_at=now
        )
        db.add(audit)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to issue token")

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 900,
        "user": {"id": user.id, "username": user.username}
    }

@router.post("/logout", status_code=204)
def logout(db: Session = Depends(get_db), principal: Principal = Depends(require_user)):
    now = int(time.time())
    principal.session.revoked_at = now
    
    audit = AuditEvent(
        user_id=principal.user.id,
        event="LOGOUT",
        outcome="SUCCESS",
        request_id=str(uuid4()),
        created_at=now
    )
    db.add(audit)
    db.commit()
    return

@router.get("/me")
def get_me(principal: Principal = Depends(require_user)):
    return {
        "id": principal.user.id,
        "username": principal.user.username,
        "session_id": principal.session.id,
        "expires_at": principal.session.expires_at
    }
