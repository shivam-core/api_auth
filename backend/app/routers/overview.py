from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Note, Document, AuthSession, AuditEvent, Envelope
from app.schemas import OverviewResponse
from app.dependencies import require_user, Principal
import time

router = APIRouter()

@router.get("", response_model=OverviewResponse)
def get_overview(db: Session = Depends(get_db), principal: Principal = Depends(require_user)):
    user_id = principal.user.id
    
    note_count = db.query(func.count(Note.id)).filter(Note.user_id == user_id).scalar() or 0
    document_count = db.query(func.count(Document.id)).filter(Document.user_id == user_id).scalar() or 0
    
    doc_storage = db.query(func.sum(Document.byte_length)).filter(Document.user_id == user_id).scalar() or 0
    
    note_storage = db.query(func.sum(func.length(Envelope.ciphertext)))\
        .join(Note, Note.envelope_id == Envelope.id)\
        .filter(Note.user_id == user_id).scalar() or 0
        
    storage_used_bytes = doc_storage + note_storage
    
    now = int(time.time())
    active_sessions = db.query(func.count(AuthSession.id)).filter(
        AuthSession.user_id == user_id,
        AuthSession.revoked_at == None,
        AuthSession.expires_at > now
    ).scalar() or 0
    
    recent_events_models = db.query(AuditEvent).filter(AuditEvent.user_id == user_id).order_by(AuditEvent.created_at.desc()).limit(10).all()
    
    return {
        "note_count": note_count,
        "document_count": document_count,
        "storage_used_bytes": storage_used_bytes,
        "active_sessions": active_sessions,
        "recent_events": [
            {
                "id": ev.id,
                "event": ev.event,
                "outcome": ev.outcome,
                "request_id": ev.request_id,
                "created_at": ev.created_at,
                "reason_code": ev.reason_code,
                "source": ev.source
            } for ev in recent_events_models
        ]
    }
