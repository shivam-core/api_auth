import time
import base64
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models import Note, Envelope, AuditEvent
from app.schemas import NoteCreate, NoteUpdate, PaginatedNotes
from app.security import encrypt_note, decrypt_note
from app.dependencies import require_user, Principal
from app.config import NOTES_AES_KEY
from cryptography.exceptions import InvalidTag

router = APIRouter()

@router.post("", status_code=201)
def create_note(note_in: NoteCreate, db: Session = Depends(get_db), principal: Principal = Depends(require_user)):
    note_id = str(uuid4())
    
    try:
        nonce, ciphertext = encrypt_note(
            title=note_in.title,
            body=note_in.body,
            user_id=principal.user.id,
            note_id=note_id,
            key=NOTES_AES_KEY
        )
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e))

    env_id = str(uuid4())
    envelope = Envelope(
        id=env_id,
        key_id="enc-v1",
        nonce=nonce,
        ciphertext=ciphertext,
        format_version=1
    )

    now = int(time.time())
    note = Note(
        id=note_id,
        user_id=principal.user.id,
        envelope_id=env_id,
        version=1,
        created_at=now,
        updated_at=now
    )
    
    audit = AuditEvent(
        user_id=principal.user.id,
        event="NOTE_CREATE",
        outcome="SUCCESS",
        request_id=str(uuid4()),
        created_at=now
    )
    
    # Retry on nonce collision up to 3 times
    for _ in range(3):
        try:
            with db.begin_nested():
                db.add(envelope)
                db.add(note)
                db.add(audit)
            db.commit()
            break
        except IntegrityError:
            # Generate new nonce
            try:
                nonce, ciphertext = encrypt_note(
                    title=note_in.title,
                    body=note_in.body,
                    user_id=principal.user.id,
                    note_id=note_id,
                    key=NOTES_AES_KEY
                )
                envelope.nonce = nonce
                envelope.ciphertext = ciphertext
            except ValueError as e:
                raise HTTPException(status_code=413, detail=str(e))
    else:
        raise HTTPException(status_code=500, detail="Failed to generate unique nonce")

    return {
        "id": note.id,
        "title": note_in.title,
        "body": note_in.body,
        "created_at": note.created_at,
        "updated_at": note.updated_at,
        "version": note.version
    }

@router.get("", response_model=PaginatedNotes)
def list_notes(limit: int = 20, offset: int = 0, db: Session = Depends(get_db), principal: Principal = Depends(require_user)):
    limit = max(1, min(limit, 50))
    offset = max(0, offset)
    
    query = db.query(Note).options(joinedload(Note.envelope)).filter(Note.user_id == principal.user.id).order_by(Note.updated_at.desc())
    total = query.count()
    notes = query.offset(offset).limit(limit).all()
    
    items = []
    for note in notes:
        try:
            decrypted = decrypt_note(note.envelope.nonce, note.envelope.ciphertext, principal.user.id, note.id, NOTES_AES_KEY, note.envelope.format_version)
            items.append({
                "id": note.id,
                "title": decrypted.get("title", ""),
                "created_at": note.created_at,
                "updated_at": note.updated_at,
                "version": note.version
            })
        except (InvalidTag, ValueError):
            now = int(time.time())
            db.add(AuditEvent(
                user_id=principal.user.id,
                event="DATA_INTEGRITY_ERROR",
                outcome="FAILURE",
                request_id=str(uuid4()),
                created_at=now,
                reason_code="INVALID_TAG_LIST"
            ))
            db.commit()
            raise HTTPException(status_code=500, detail="DATA_INTEGRITY_ERROR")
            
    return {"items": items, "total": total, "limit": limit, "offset": offset}

@router.get("/{id}")
def get_note(id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_user)):
    note = db.query(Note).options(joinedload(Note.envelope)).filter(Note.id == id, Note.user_id == principal.user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Not found")
        
    try:
        decrypted = decrypt_note(note.envelope.nonce, note.envelope.ciphertext, principal.user.id, note.id, NOTES_AES_KEY, note.envelope.format_version)
    except (InvalidTag, ValueError):
        now = int(time.time())
        db.add(AuditEvent(
            user_id=principal.user.id,
            event="DATA_INTEGRITY_ERROR",
            outcome="FAILURE",
            request_id=str(uuid4()),
            created_at=now,
            reason_code="INVALID_TAG_READ"
        ))
        db.commit()
        raise HTTPException(status_code=500, detail="DATA_INTEGRITY_ERROR")
        
    return {
        "id": note.id,
        "title": decrypted.get("title", ""),
        "body": decrypted.get("body", ""),
        "created_at": note.created_at,
        "updated_at": note.updated_at,
        "version": note.version
    }

@router.patch("/{id}")
def update_note(id: str, note_in: NoteUpdate, db: Session = Depends(get_db), principal: Principal = Depends(require_user)):
    # Lock row to prevent concurrent updates breaking nonce constraints
    note = db.query(Note).options(joinedload(Note.envelope)).filter(Note.id == id, Note.user_id == principal.user.id).with_for_update().first()
    if not note:
        raise HTTPException(status_code=404, detail="Not found")
        
    try:
        nonce, ciphertext = encrypt_note(
            title=note_in.title,
            body=note_in.body,
            user_id=principal.user.id,
            note_id=note.id,
            key=NOTES_AES_KEY
        )
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e))

    now = int(time.time())
    note.envelope.nonce = nonce
    note.envelope.ciphertext = ciphertext
    note.envelope.format_version = 1
    note.version += 1
    note.updated_at = now
    
    audit = AuditEvent(
        user_id=principal.user.id,
        event="NOTE_UPDATE",
        outcome="SUCCESS",
        request_id=str(uuid4()),
        created_at=now
    )
    
    for _ in range(3):
        try:
            with db.begin_nested():
                db.add(audit)
            db.commit()
            break
        except IntegrityError:
            try:
                nonce, ciphertext = encrypt_note(
                    title=note_in.title,
                    body=note_in.body,
                    user_id=principal.user.id,
                    note_id=note.id,
                    key=NOTES_AES_KEY
                )
                note.envelope.nonce = nonce
                note.envelope.ciphertext = ciphertext
            except ValueError as e:
                raise HTTPException(status_code=413, detail=str(e))
    else:
        raise HTTPException(status_code=500, detail="Failed to generate unique nonce")

    return {
        "id": note.id,
        "title": note_in.title,
        "body": note_in.body,
        "created_at": note.created_at,
        "updated_at": note.updated_at,
        "version": note.version
    }

@router.delete("/{id}", status_code=204)
def delete_note(id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_user)):
    note = db.query(Note).filter(Note.id == id, Note.user_id == principal.user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Not found")
    
    now = int(time.time())
    if note.envelope:
        db.delete(note.envelope)
    db.delete(note)
    
    audit = AuditEvent(
        user_id=principal.user.id,
        event="NOTE_DELETE",
        outcome="SUCCESS",
        request_id=str(uuid4()),
        created_at=now
    )
    db.add(audit)
    db.commit()
    return

@router.get("/{id}/envelope")
def get_note_envelope(id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_user)):
    note = db.query(Note).options(joinedload(Note.envelope)).filter(Note.id == id, Note.user_id == principal.user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Not found")
        
    return {
        "key_id": note.envelope.key_id,
        "nonce_b64": base64.b64encode(note.envelope.nonce).decode('ascii'),
        "ciphertext_b64": base64.b64encode(note.envelope.ciphertext).decode('ascii'),
        "byte_count": len(note.envelope.ciphertext),
        "version": note.version
    }
