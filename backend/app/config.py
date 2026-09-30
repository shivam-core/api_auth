from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey

class Settings(BaseSettings):
    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./ciphergate.db"
    
    JWT_PRIVATE_KEY_PATH: Optional[str] = None
    JWT_PUBLIC_KEY_PATH: Optional[str] = None
    NOTES_KEY_PATH: Optional[str] = None

    JWT_PRIVATE_KEY_B64: Optional[str] = None
    JWT_PUBLIC_KEY_B64: Optional[str] = None
    NOTES_KEY_B64: Optional[str] = None

    ALLOWED_HOSTS: str = "localhost,127.0.0.1"

    class Config:
        env_file = ".env"

settings = Settings()

# Resolve paths against the repository root
repo_root = Path(__file__).parent.parent.parent

def _load_key(path: Optional[str], b64: Optional[str]) -> bytes:
    if b64:
        return base64.b64decode(b64)
    if path:
        file_path = repo_root / path
        if file_path.exists():
            return file_path.read_bytes()
    raise ValueError("Missing or inconsistent key configuration")

try:
    private_key_bytes = _load_key(settings.JWT_PRIVATE_KEY_PATH, settings.JWT_PRIVATE_KEY_B64)
    public_key_bytes = _load_key(settings.JWT_PUBLIC_KEY_PATH, settings.JWT_PUBLIC_KEY_B64)
    notes_key_b64_bytes = _load_key(settings.NOTES_KEY_PATH, settings.NOTES_KEY_B64)
    
    # Verify RSA keys
    private_key = serialization.load_pem_private_key(private_key_bytes, password=None)
    public_key = serialization.load_pem_public_key(public_key_bytes)
    
    if not isinstance(private_key, RSAPrivateKey) or not isinstance(public_key, RSAPublicKey):
        raise ValueError("Keys must be RSA")
        
    if private_key.key_size < 3072 or public_key.key_size < 3072:
        raise ValueError("RSA keys must be at least 3072 bits")

    # Verify they form a pair
    expected_public_numbers = private_key.public_key().public_numbers()
    if public_key.public_numbers() != expected_public_numbers:
        raise ValueError("RSA public and private keys do not match")

    # The file contents / b64 env var might be raw bytes or base64 encoded string
    if len(notes_key_b64_bytes) == 32:
        NOTES_AES_KEY = notes_key_b64_bytes
    else:
        NOTES_AES_KEY = base64.b64decode(notes_key_b64_bytes.strip())
    
    if len(NOTES_AES_KEY) != 32:
        raise ValueError("Invalid AES key length")
except Exception as e:
    import sys
    print(f"Startup fails safely: {e}", file=sys.stderr)
    sys.exit(1)
