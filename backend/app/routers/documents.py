import time
import base64
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models import Document, Envelope, AuditEvent
from app.schemas import DocumentResponse, PaginatedDocuments, DocumentUpdate, DocumentEnvelopeResponse
from app.security import encrypt_document_metadata, decrypt_document_metadata, encrypt_document_content, decrypt_document_content
from app.dependencies import require_user, Principal
from app.config import NOTES_AES_KEY
from cryptography.exceptions import InvalidTag

router = APIRouter()

@router.post("", status_code=201)
async def create_document(
    file: UploadFile = File(...),
    display_name: str = Form(None),
    description: str = Form(None),
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_user)
):
    content = await file.read()
    doc_id = str(uuid4())
    display_name = display_name or file.filename
    description = description or ""
    
    try:
        meta_nonce, meta_cipher = encrypt_document_metadata(
            filename=file.filename,
            display_name=display_name,
            description=description,
            user_id=principal.user.id,
            document_id=doc_id,
            key=NOTES_AES_KEY
        )
        
        cont_nonce, cont_cipher = encrypt_document_content(
            content_bytes=content,
            user_id=principal.user.id,
            document_id=doc_id,
            key=NOTES_AES_KEY
        )
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e))
    
    meta_env_id = str(uuid4())
    cont_env_id = str(uuid4())
    
    meta_env = Envelope(id=meta_env_id, key_id="enc-v1", nonce=meta_nonce, ciphertext=meta_cipher, format_version=1)
    cont_env = Envelope(id=cont_env_id, key_id="enc-v1", nonce=cont_nonce, ciphertext=cont_cipher, format_version=1)
    
    now = int(time.time())
    doc = Document(
        id=doc_id,
        user_id=principal.user.id,
        metadata_envelope_id=meta_env_id,
        content_envelope_id=cont_env_id,
        byte_length=len(content),
        media_type=file.content_type or "application/octet-stream",
        created_at=now,
        updated_at=now,
        version=1
    )
    
    audit = AuditEvent(
        user_id=principal.user.id,
        event="DOCUMENT_CREATE",
        outcome="SUCCESS",
        request_id=str(uuid4()),
        created_at=now
    )
    
    for _ in range(3):
        try:
            with db.begin_nested():
                db.add(meta_env)
                db.add(cont_env)
                db.add(doc)
                db.add(audit)
            db.commit()
            break
        except IntegrityError:
            # Simple retry, though highly unlikely with uuid4
            pass
    else:
        raise HTTPException(status_code=500, detail="Failed to create document")
    
    return {
        "id": doc.id,
        "filename": file.filename,
        "display_name": display_name,
        "description": description,
        "byte_length": doc.byte_length,
        "media_type": doc.media_type,
        "created_at": doc.created_at,
        "updated_at": doc.updated_at,
        "version": doc.version
    }

@router.get("", response_model=PaginatedDocuments)
def list_documents(limit: int = 20, offset: int = 0, db: Session = Depends(get_db), principal: Principal = Depends(require_user)):
    limit = max(1, min(limit, 50))
    offset = max(0, offset)
    
    query = db.query(Document).options(joinedload(Document.metadata_envelope)).filter(Document.user_id == principal.user.id).order_by(Document.updated_at.desc())
    total = query.count()
    documents = query.offset(offset).limit(limit).all()
    
    items = []
    for doc in documents:
        try:
            decrypted = decrypt_document_metadata(doc.metadata_envelope.nonce, doc.metadata_envelope.ciphertext, principal.user.id, doc.id, NOTES_AES_KEY)
            items.append({
                "id": doc.id,
                "filename": decrypted.get("filename", ""),
                "display_name": decrypted.get("display_name", ""),
                "description": decrypted.get("description", ""),
                "byte_length": doc.byte_length,
                "media_type": doc.media_type,
                "created_at": doc.created_at,
                "updated_at": doc.updated_at,
                "version": doc.version
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

@router.get("/{id}", response_model=DocumentResponse)
def get_document(id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_user)):
    doc = db.query(Document).options(joinedload(Document.metadata_envelope)).filter(Document.id == id, Document.user_id == principal.user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
        
    try:
        decrypted = decrypt_document_metadata(doc.metadata_envelope.nonce, doc.metadata_envelope.ciphertext, principal.user.id, doc.id, NOTES_AES_KEY)
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
        "id": doc.id,
        "filename": decrypted.get("filename", ""),
        "display_name": decrypted.get("display_name", ""),
        "description": decrypted.get("description", ""),
        "byte_length": doc.byte_length,
        "media_type": doc.media_type,
        "created_at": doc.created_at,
        "updated_at": doc.updated_at,
        "version": doc.version
    }

@router.get("/{id}/content")
def get_document_content(id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_user)):
    doc = db.query(Document).options(joinedload(Document.content_envelope)).filter(Document.id == id, Document.user_id == principal.user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
        
    try:
        content_bytes = decrypt_document_content(doc.content_envelope.nonce, doc.content_envelope.ciphertext, principal.user.id, doc.id, NOTES_AES_KEY)
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
        
    return Response(content=content_bytes, media_type=doc.media_type)

@router.patch("/{id}", response_model=DocumentResponse)
def update_document(id: str, doc_in: DocumentUpdate, db: Session = Depends(get_db), principal: Principal = Depends(require_user)):
    doc = db.query(Document).options(joinedload(Document.metadata_envelope)).filter(Document.id == id, Document.user_id == principal.user.id).with_for_update().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
        
    try:
        decrypted = decrypt_document_metadata(doc.metadata_envelope.nonce, doc.metadata_envelope.ciphertext, principal.user.id, doc.id, NOTES_AES_KEY)
    except (InvalidTag, ValueError):
        raise HTTPException(status_code=500, detail="DATA_INTEGRITY_ERROR")
        
    if doc_in.display_name is not None:
        decrypted["display_name"] = doc_in.display_name
    if doc_in.description is not None:
        decrypted["description"] = doc_in.description
        
    try:
        nonce, ciphertext = encrypt_document_metadata(
            filename=decrypted.get("filename", ""),
            display_name=decrypted["display_name"],
            description=decrypted["description"],
            user_id=principal.user.id,
            document_id=doc.id,
            key=NOTES_AES_KEY
        )
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e))
    
    now = int(time.time())
    doc.metadata_envelope.nonce = nonce
    doc.metadata_envelope.ciphertext = ciphertext
    doc.version += 1
    doc.updated_at = now
    
    audit = AuditEvent(
        user_id=principal.user.id,
        event="DOCUMENT_UPDATE",
        outcome="SUCCESS",
        request_id=str(uuid4()),
        created_at=now
    )
    db.add(audit)
    db.commit()
    
    return {
        "id": doc.id,
        "filename": decrypted.get("filename", ""),
        "display_name": decrypted["display_name"],
        "description": decrypted["description"],
        "byte_length": doc.byte_length,
        "media_type": doc.media_type,
        "created_at": doc.created_at,
        "updated_at": doc.updated_at,
        "version": doc.version
    }

@router.delete("/{id}", status_code=204)
def delete_document(id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_user)):
    doc = db.query(Document).options(joinedload(Document.metadata_envelope), joinedload(Document.content_envelope)).filter(Document.id == id, Document.user_id == principal.user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    
    now = int(time.time())
    if doc.metadata_envelope:
        db.delete(doc.metadata_envelope)
    if doc.content_envelope:
        db.delete(doc.content_envelope)
    db.delete(doc)
    
    audit = AuditEvent(
        user_id=principal.user.id,
        event="DOCUMENT_DELETE",
        outcome="SUCCESS",
        request_id=str(uuid4()),
        created_at=now
    )
    db.add(audit)
    db.commit()
    return

@router.get("/{id}/envelope", response_model=DocumentEnvelopeResponse)
def get_document_envelope(id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_user)):
    doc = db.query(Document).options(joinedload(Document.metadata_envelope), joinedload(Document.content_envelope)).filter(Document.id == id, Document.user_id == principal.user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
        
    return {
        "key_id": doc.metadata_envelope.key_id,
        "metadata_nonce_b64": base64.b64encode(doc.metadata_envelope.nonce).decode('ascii'),
        "metadata_ciphertext_b64": base64.b64encode(doc.metadata_envelope.ciphertext).decode('ascii'),
        "content_nonce_b64": base64.b64encode(doc.content_envelope.nonce).decode('ascii'),
        "content_byte_count": len(doc.content_envelope.ciphertext),
        "version": doc.version
    }
