from fastapi import APIRouter
from app.schemas import ExperimentResponse
from uuid import uuid4
import time
from argon2 import PasswordHasher, Type
import jwt
from app.config import private_key_bytes, public_key_bytes, NOTES_AES_KEY
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
import secrets
import statistics

router = APIRouter()

@router.post("/bruteforce", response_model=ExperimentResponse)
def experiment_bruteforce():
    start = time.time()
    ph = PasswordHasher(
        time_cost=2, memory_cost=19456, parallelism=1,
        hash_len=32, salt_len=16, type=Type.ID,
    )
    # Simulate 5 hashing attempts
    for _ in range(5):
        ph.hash("supersecretpassword123")
    duration = int((time.time() - start) * 1000)
    
    return {
        "experiment": "bruteforce",
        "mode": "offline",
        "expected": "Slow execution proving memory hardness",
        "observed": f"5 iterations took {duration}ms",
        "passed": duration > 100,  # Arbitrary threshold to prove it's not instantaneous
        "duration_ms": duration,
        "explanation": "Argon2id configuration enforces high memory and CPU cost.",
        "request_id": str(uuid4())
    }

@router.post("/timing", response_model=ExperimentResponse)
def experiment_timing():
    # Measure valid vs invalid JWT signature verification
    token = jwt.encode({"test": 1, "exp": int(time.time()) + 3600}, private_key_bytes, algorithm="RS256")
    invalid_token = token[:-5] + "aaaaa"
    
    valid_times = []
    for _ in range(100):
        t0 = time.time()
        try:
            jwt.decode(token, public_key_bytes, algorithms=["RS256"])
        except Exception:
            pass
        valid_times.append(time.time() - t0)
        
    invalid_times = []
    for _ in range(100):
        t0 = time.time()
        try:
            jwt.decode(invalid_token, public_key_bytes, algorithms=["RS256"])
        except Exception:
            pass
        invalid_times.append(time.time() - t0)
        
    mean_valid = statistics.mean(valid_times) * 1000
    mean_invalid = statistics.mean(invalid_times) * 1000
    
    diff = abs(mean_valid - mean_invalid)
    passed = diff < 1.0  # Difference should be very small (< 1ms)
    
    return {
        "experiment": "timing",
        "mode": "online",
        "expected": "Constant time comparison, diff < 1ms",
        "observed": f"Valid: {mean_valid:.3f}ms, Invalid: {mean_invalid:.3f}ms. Diff: {diff:.3f}ms",
        "passed": passed,
        "duration_ms": int((sum(valid_times) + sum(invalid_times)) * 1000),
        "explanation": "cryptography uses constant-time comparison for signatures.",
        "request_id": str(uuid4())
    }

@router.post("/fuzz", response_model=ExperimentResponse)
def experiment_fuzz():
    start = time.time()
    aesgcm = AESGCM(NOTES_AES_KEY)
    nonce = secrets.token_bytes(12)
    # Valid encryption
    ciphertext = aesgcm.encrypt(nonce, b"data", b"aad")
    
    # Fuzzing
    passed = True
    fuzz_count = 0
    # Change AAD
    try:
        aesgcm.decrypt(nonce, ciphertext, b"bad_aad")
        passed = False
    except InvalidTag:
        fuzz_count += 1
        
    # Change nonce
    try:
        aesgcm.decrypt(secrets.token_bytes(12), ciphertext, b"aad")
        passed = False
    except InvalidTag:
        fuzz_count += 1
        
    # Truncate ciphertext
    try:
        aesgcm.decrypt(nonce, ciphertext[:-1], b"aad")
        passed = False
    except InvalidTag:
        fuzz_count += 1
        
    duration = int((time.time() - start) * 1000)
    
    return {
        "experiment": "fuzz",
        "mode": "online",
        "expected": "InvalidTag raised on all modifications",
        "observed": f"Caught {fuzz_count}/3 modifications",
        "passed": passed,
        "duration_ms": duration,
        "explanation": "AES-GCM authenticates the ciphertext and AAD.",
        "request_id": str(uuid4())
    }
