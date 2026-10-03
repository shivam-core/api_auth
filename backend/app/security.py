import base64
import json
import secrets
import time
from uuid import UUID, uuid4

import jwt
from argon2 import PasswordHasher, Type
from argon2.exceptions import (
    InvalidHashError, VerificationError, VerifyMismatchError,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ISSUER = "urn:ciphergate:auth"
AUDIENCE = "urn:ciphergate:api"
SIGNING_KID = "sig-v1"
ENCRYPTION_KID = "enc-v1"
TOKEN_TTL = 900
PH = PasswordHasher(
    time_cost=2, memory_cost=19456, parallelism=1,
    hash_len=32, salt_len=16, type=Type.ID,
)

def hash_password(password: str) -> str:
    return PH.hash(password)

def verify_password(encoded: str, password: str) -> bool:
    try:
        return PH.verify(encoded, password)
    except (VerifyMismatchError, VerificationError,
            InvalidHashError):
        return False

def issue_access_token(user_id, session_id, private_key):
    now = int(time.time())
    claims = {
        "iss": ISSUER, "aud": AUDIENCE,
        "sub": str(UUID(user_id)),
        "sid": str(UUID(session_id)),
        "jti": str(uuid4()),
        "iat": now, "nbf": now, "exp": now + TOKEN_TTL,
    }
    token = jwt.encode(
        claims, private_key, algorithm="RS256",
        headers={"kid": SIGNING_KID, "typ": "JWT"},
    )
    return token, claims["exp"]

def verify_access_token(token: str, public_key) -> dict:
    if not isinstance(token, str) or len(token) > 8192:
        raise jwt.InvalidTokenError("Invalid token size")
    header = jwt.get_unverified_header(token)
    if (header.get("alg") != "RS256"
        or header.get("typ") != "JWT"
        or header.get("kid") != SIGNING_KID):
        raise jwt.InvalidTokenError("Unexpected header")
    if any(name in header for name in ("jku", "x5u", "crit")):
        raise jwt.InvalidTokenError("Unsupported header")
    claims = jwt.decode(
        token, public_key, algorithms=["RS256"],
        issuer=ISSUER, audience=AUDIENCE, leeway=0,
        options={"require": [
            "iss", "aud", "sub", "sid", "jti",
            "iat", "nbf", "exp",
        ]},
    )
    for name in ("iat", "nbf", "exp"):
        if type(claims[name]) is not int:
            raise jwt.InvalidTokenError("Invalid time type")
    duration = claims["exp"] - claims["iat"]
    if not 0 < duration <= TOKEN_TTL:
        raise jwt.InvalidTokenError("Invalid lifetime")
    if claims["nbf"] != claims["iat"]:
        raise jwt.InvalidTokenError("Invalid start time")
    try:
        for name in ("sub", "sid", "jti"):
            value = claims[name]
            if not isinstance(value, str):
                raise ValueError("Not a string")
            if str(UUID(value)) != value:
                raise ValueError("Not a canonical UUID")
    except (ValueError, TypeError, AttributeError) as exc:
        raise jwt.InvalidTokenError("Invalid identifier") from exc
    return claims

def note_aad_v0(user_id: str, note_id: str) -> bytes:
    owner = str(UUID(user_id))
    note = str(UUID(note_id))
    return f"ciphergate:note:v1:{owner}:{note}".encode("ascii")

def note_aad_v1(user_id: str, note_id: str) -> bytes:
    owner = str(UUID(user_id))
    note = str(UUID(note_id))
    arr = ["ciphergate", 1, "note", owner, note, "content"]
    return json.dumps(arr, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

def get_note_aad(user_id: str, note_id: str, format_version: int) -> bytes:
    if format_version == 0:
        return note_aad_v0(user_id, note_id)
    elif format_version == 1:
        return note_aad_v1(user_id, note_id)
    else:
        raise ValueError("Unknown envelope format version")

def encrypt_note(title, body, user_id, note_id, key):
    if len(key) != 32:
        raise ValueError("AES key must contain 32 bytes")
    payload = json.dumps(
        {"title": title, "body": body},
        ensure_ascii=False, separators=(",", ":"),
    ).encode("utf-8")
    if len(payload) > 50 * 1024:
        raise ValueError("Note payload too large")
    nonce = secrets.token_bytes(12)
    ciphertext = AESGCM(key).encrypt(
        nonce, payload, get_note_aad(user_id, note_id, 1),
    )
    return nonce, ciphertext

def decrypt_note(nonce, ciphertext, user_id, note_id, key, format_version=0):
    if len(key) != 32 or len(nonce) != 12:
        raise ValueError("Invalid encryption parameters")
    plaintext = AESGCM(key).decrypt(
        nonce, ciphertext, get_note_aad(user_id, note_id, format_version),
    )
    return json.loads(plaintext.decode("utf-8"))

def document_aad(user_id: str, document_id: str, field: str) -> bytes:
    owner = str(UUID(user_id))
    doc = str(UUID(document_id))
    arr = ["ciphergate", 1, "document", owner, doc, field]
    return json.dumps(arr, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

def encrypt_document_metadata(filename: str, display_name: str, description: str, user_id: str, document_id: str, key: bytes):
    if len(key) != 32:
        raise ValueError("AES key must contain 32 bytes")
    payload = json.dumps(
        {"filename": filename, "display_name": display_name, "description": description},
        ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    nonce = secrets.token_bytes(12)
    ciphertext = AESGCM(key).encrypt(nonce, payload, document_aad(user_id, document_id, "metadata"))
    return nonce, ciphertext

def decrypt_document_metadata(nonce, ciphertext, user_id, document_id, key):
    if len(key) != 32 or len(nonce) != 12:
        raise ValueError("Invalid encryption parameters")
    plaintext = AESGCM(key).decrypt(nonce, ciphertext, document_aad(user_id, document_id, "metadata"))
    return json.loads(plaintext.decode("utf-8"))

def encrypt_document_content(content_bytes: bytes, user_id: str, document_id: str, key: bytes):
    if len(key) != 32:
        raise ValueError("AES key must contain 32 bytes")
    if len(content_bytes) > 2 * 1024 * 1024:
        raise ValueError("Document payload too large")
    nonce = secrets.token_bytes(12)
    ciphertext = AESGCM(key).encrypt(nonce, content_bytes, document_aad(user_id, document_id, "content"))
    return nonce, ciphertext

def decrypt_document_content(nonce, ciphertext, user_id, document_id, key):
    if len(key) != 32 or len(nonce) != 12:
        raise ValueError("Invalid encryption parameters")
    return AESGCM(key).decrypt(nonce, ciphertext, document_aad(user_id, document_id, "content"))

def load_aes_key(encoded: str) -> bytes:
    key = base64.b64decode(encoded, validate=True)
    if len(key) != 32:
        raise ValueError("Invalid AES key length")
    return key
