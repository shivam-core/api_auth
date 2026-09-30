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
    body: str = Field(min_length=1, max_length=5000)

    class Config:
        extra = 'forbid'

class NoteUpdate(NoteCreate):
    pass

class NoteSummaryResponse(BaseModel):
    id: str
    title: str
    created_at: int
    updated_at: int

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

class AuditEventResponse(BaseModel):
    id: str
    event: str
    outcome: str
    request_id: str
    created_at: int
    reason_code: Optional[str]

class PaginatedAuditEvents(BaseModel):
    items: List[AuditEventResponse]
    total: int
    limit: int
    offset: int
