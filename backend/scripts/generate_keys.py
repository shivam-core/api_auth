from pathlib import Path
import base64
import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

os.umask(0o077)
# Resolve path relative to repository root assuming this runs from backend/scripts/generate_keys.py
directory = Path(__file__).parent.parent.parent / ".secrets"
directory.mkdir(mode=0o700, exist_ok=True)
paths = [directory / name for name in (
    "jwt-private.pem", "jwt-public.pem", "notes-key.b64",
)]
if any(path.exists() for path in paths):
    raise SystemExit("Refusing to overwrite existing keys")

private = rsa.generate_private_key(
    public_exponent=65537, key_size=3072,
)
private_bytes = private.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption(),
)
public_bytes = private.public_key().public_bytes(
    serialization.Encoding.PEM,
    serialization.PublicFormat.SubjectPublicKeyInfo,
)
values = [private_bytes, public_bytes,
          base64.b64encode(AESGCM.generate_key(bit_length=256))]
for path, value in zip(paths, values):
    with path.open("xb") as stream:
        stream.write(value)
print("Created local key files; keep them outside version control.")
