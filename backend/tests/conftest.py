import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
import os
import tempfile
import uuid

# Before importing app, set env vars to ensure we don't load real secrets or DB
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
# Generate dummy keys for tests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64

private = rsa.generate_private_key(public_exponent=65537, key_size=3072)
private_bytes = private.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption(),
)
public_bytes = private.public_key().public_bytes(
    serialization.Encoding.PEM,
    serialization.PublicFormat.SubjectPublicKeyInfo,
)
notes_key = base64.b64encode(AESGCM.generate_key(bit_length=256))

os.environ["JWT_PRIVATE_KEY_B64"] = base64.b64encode(private_bytes).decode('ascii')
os.environ["JWT_PUBLIC_KEY_B64"] = base64.b64encode(public_bytes).decode('ascii')
os.environ["NOTES_KEY_B64"] = notes_key.decode('ascii')
os.environ["APP_ENV"] = "test"

from app.main import app
from app.database import Base, get_db

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        # Enforce foreign keys manually for sqlite memory DB in test
        db.execute("PRAGMA foreign_keys=ON")
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def client():
    # Clear DB before each test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
def clear_rate_limits():
    from app.rate_limit import limiter
    limiter.ip_login_attempts.clear()
    limiter.username_failed_attempts.clear()
    limiter.ip_register_attempts.clear()
