from sqlalchemy import Column, String, Boolean, BigInteger, LargeBinary, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(BigInteger, nullable=False)

class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(BigInteger, nullable=False)
    expires_at = Column(BigInteger, nullable=False)
    revoked_at = Column(BigInteger, nullable=True)

    __table_args__ = (
        Index("ix_auth_sessions_user_id_expires_at", "user_id", "expires_at"),
    )

class Envelope(Base):
    __tablename__ = "envelopes"

    id = Column(String, primary_key=True, default=generate_uuid)
    key_id = Column(String, nullable=False)
    nonce = Column(LargeBinary, nullable=False)
    ciphertext = Column(LargeBinary, nullable=False)
    format_version = Column(BigInteger, nullable=False, default=1)

    __table_args__ = (
        UniqueConstraint("key_id", "nonce", name="uq_envelopes_key_id_nonce"),
    )

class Note(Base):
    __tablename__ = "notes"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    envelope_id = Column(String, ForeignKey("envelopes.id"), nullable=False)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)
    version = Column(BigInteger, nullable=False, default=1)

    envelope = relationship("Envelope")

    __table_args__ = (
        Index("ix_notes_user_id_updated_at", "user_id", "updated_at"),
    )

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    metadata_envelope_id = Column(String, ForeignKey("envelopes.id"), nullable=False)
    content_envelope_id = Column(String, ForeignKey("envelopes.id"), nullable=False)
    byte_length = Column(BigInteger, nullable=False)
    media_type = Column(String, nullable=False)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)
    version = Column(BigInteger, nullable=False, default=1)

    metadata_envelope = relationship("Envelope", foreign_keys=[metadata_envelope_id])
    content_envelope = relationship("Envelope", foreign_keys=[content_envelope_id])

    __table_args__ = (
        Index("ix_documents_user_id_updated_at", "user_id", "updated_at"),
    )

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    event = Column(String, nullable=False)
    outcome = Column(String, nullable=False)
    request_id = Column(String, nullable=False)
    created_at = Column(BigInteger, nullable=False)
    reason_code = Column(String, nullable=True)
    source = Column(String, nullable=False, default="user")

    __table_args__ = (
        Index("ix_audit_events_user_id_created_at", "user_id", "created_at"),
    )
