from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AuditEvent
from app.schemas import PaginatedAuditEvents
from app.dependencies import require_user, Principal

router = APIRouter()

@router.get("", response_model=PaginatedAuditEvents)
def list_audit_events(limit: int = 20, offset: int = 0, db: Session = Depends(get_db), principal: Principal = Depends(require_user)):
    limit = max(1, min(limit, 50))
    offset = max(0, offset)
    
    query = db.query(AuditEvent).filter(AuditEvent.user_id == principal.user.id).order_by(AuditEvent.created_at.desc())
    total = query.count()
    events = query.offset(offset).limit(limit).all()
    
    items = [{
        "id": e.id,
        "event": e.event,
        "outcome": e.outcome,
        "request_id": e.request_id,
        "created_at": e.created_at,
        "reason_code": e.reason_code
    } for e in events]
    
    return {"items": items, "total": total, "limit": limit, "offset": offset}
