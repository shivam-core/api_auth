# Secure API Authentication System (CipherGate)

**Author:** Shivam Kore
**PRN:** 25030421041
**Date:** 30 September 2026

## 1. Problem Statement and Objectives
Web APIs must distinguish valid users from unauthorized callers, detect modified credentials, restrict each user to permitted resources, and protect sensitive data in transit and storage. This project aims to implement a token-based authentication system providing these controls for a private notes application.

## 2. Scope & Requirements
- **In-scope**: Registration and Login (Username/Password), JWT access tokens (RS256, 15-min life), DB session tracking and revocation, AES-256-GCM encryption of notes, API playground.
- **Out-of-scope**: Email verification, refresh tokens, password reset, OAuth, sharing/teams.

## 3. Threat Model & Limitations
- **Password theft**: Mitigated by Argon2id hashing. However, weak passwords can still be guessed offline.
- **Token modification**: Prevented by strict RS256 signature verification.
- **Cross-user access**: Prevented by database ownership checks (authorization).
- **Note database theft**: Notes are AES-256-GCM encrypted. However, metadata (times, IDs, lengths) remains visible, and a full server compromise exposes keys.
- **Network interception**: Prevented by HTTPS TLS deployment.

## 4. Architecture
The system uses a monolithic architecture. React (TypeScript, Vite) serves the frontend. FastAPI serves the API and the compiled frontend assets. The DB (SQLite locally, PostgreSQL hosted) stores data. 

- **Hashing**: Argon2id for password hashes.
- **Authentication**: JWTs signed with RS256 using a 3072-bit RSA private key.
- **Encryption**: AES-256-GCM with a 32-byte secret key for note payloads.

## 5. Implementation Summary
The API follows RESTful patterns with explicit validation. Tokens are stored in memory on the client side to minimize XSS and CSRF risks.

## 6. Result Analysis
- **Token Tampering Tests**: The backend successfully rejects invalid JWTs, modified payloads without resignatures, or incorrect algorithms.
- **Ciphertext Integrity**: Attempting to alter a ciphertext byte causes an `InvalidTag` exception and the server returns a 500 error instead of bad plaintext.
- **Concurrency**: `rate_limit.py` protects against high-volume attacks and throttles expensive Argon2 operations.
