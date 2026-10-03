from pydantic import BaseModel, Field, constr
from typing import Optional, List

class UserCreate(BaseModel):
    username: str = Field(pattern=r"^[a-z0-9_]{3,32}$")
    password: str = Field(min_length=12, max_length=128)

    class Config:
        extra = 'forbid'

class UserResponse(BaseModel):
    id: str
    username: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class SessionResponse(BaseModel):
    id: str
    created_at: int
    expires_at: int
    revoked_at: Optional[int]

class PaginatedSessions(BaseModel):
    items: List[SessionResponse]
    total: int
    limit: int
    offset: int

class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    body: str = Field(min_length=1, max_length=50000)

    class Config:
        extra = 'forbid'

class NoteUpdate(NoteCreate):
    pass

class NoteSummaryResponse(BaseModel):
    id: str
    title: str
    created_at: int
    updated_at: int
    version: int

class NoteResponse(NoteSummaryResponse):
    body: str

class PaginatedNotes(BaseModel):
    items: List[NoteSummaryResponse]
    total: int
    limit: int
    offset: int

class NoteEnvelopeResponse(BaseModel):
    key_id: str
    nonce_b64: str
    ciphertext_b64: str
    byte_count: int
    version: int

class DocumentResponse(BaseModel):
    id: str
    filename: str
    display_name: str
    description: Optional[str]
    byte_length: int
    media_type: str
    created_at: int
    updated_at: int
    version: int

class PaginatedDocuments(BaseModel):
    items: List[DocumentResponse]
    total: int
    limit: int
    offset: int

class DocumentUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = Field(None, max_length=1000)

class DocumentEnvelopeResponse(BaseModel):
    key_id: str
    metadata_nonce_b64: str
    metadata_ciphertext_b64: str
    content_nonce_b64: str
    content_byte_count: int
    version: int

class AuditEventResponse(BaseModel):
    id: str
    event: str
    outcome: str
    request_id: str
    created_at: int
    reason_code: Optional[str]
    source: str

class PaginatedAuditEvents(BaseModel):
    items: List[AuditEventResponse]
    total: int
    limit: int
    offset: int

class OverviewResponse(BaseModel):
    note_count: int
    document_count: int
    storage_used_bytes: int
    active_sessions: int
    recent_events: List[AuditEventResponse]

class ExperimentResponse(BaseModel):
    experiment: str
    mode: str
    expected: str
    observed: str
    passed: bool
    duration_ms: Optional[int]
    explanation: str
    request_id: str

class SecurityInfoResponse(BaseModel):
    authentication: str
    session_management: str
    encryption: str
    rate_limiting: str
