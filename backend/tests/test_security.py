from uuid import uuid4
import pytest
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.security import encrypt_note, decrypt_note

def test_ciphertext_tampering_is_rejected():
    user_id, note_id = str(uuid4()), str(uuid4())
    key = AESGCM.generate_key(bit_length=256)
    nonce, ciphertext = encrypt_note(
        "Revision", "RSA signs tokens", user_id, note_id, key,
    )
    changed = bytearray(ciphertext)
    changed[0] ^= 1
    with pytest.raises(InvalidTag):
        decrypt_note(nonce, bytes(changed), user_id, note_id, key)
