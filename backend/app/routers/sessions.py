import time
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AuthSession, AuditEvent
from app.schemas import PaginatedSessions
from app.dependencies import require_user, Principal

router = APIRouter()

@router.get("", response_model=PaginatedSessions)
def list_sessions(limit: int = 20, offset: int = 0, db: Session = Depends(get_db), principal: Principal = Depends(require_user)):
    limit = max(1, min(limit, 50))
    offset = max(0, offset)
    
    query = db.query(AuthSession).filter(AuthSession.user_id == principal.user.id).order_by(AuthSession.created_at.desc())
    total = query.count()
    sessions = query.offset(offset).limit(limit).all()
    
    items = [{
        "id": s.id,
        "created_at": s.created_at,
        "expires_at": s.expires_at,
        "revoked_at": s.revoked_at
    } for s in sessions]
    
    return {"items": items, "total": total, "limit": limit, "offset": offset}

@router.delete("/{id}", status_code=204)
def revoke_session(id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_user)):
    session = db.query(AuthSession).filter(AuthSession.id == id, AuthSession.user_id == principal.user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Not found")
        
    now = int(time.time())
    if session.revoked_at is None:
        session.revoked_at = now
        
        audit = AuditEvent(
            user_id=principal.user.id,
            event="SESSION_REVOKE",
            outcome="SUCCESS",
            request_id=str(uuid4()),
            created_at=now
        )
        db.add(audit)
        db.commit()
        
    return
