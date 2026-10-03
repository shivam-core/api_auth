# CipherGate Architecture

## Overview
CipherGate is a secure API authentication system leveraging modern cryptographic techniques. The primary goals are secure user authentication, robust session management, and encrypted data storage with cryptographic authenticity guarantees.

## Token-Based Authentication
Authentication is managed via JSON Web Tokens (JWT) signed with RSA-PSS (RS256 algorithm) using an asymmetric key pair. 
- The private key is used to sign tokens on login.
- The public key is used by the backend to verify the integrity and origin of the token.
- Tokens contain the `sub` (subject/user id) and an `exp` (expiration) claim.

## Envelopes Model
All encrypted objects (Notes, Documents) are encapsulated using the `Envelope` model.
An `Envelope` stores:
- `key_id`: The version/identifier of the key used for encryption (e.g., `enc-v1`).
- `nonce`: A unique 12-byte initialization vector per encryption operation.
- `ciphertext`: The AES-256-GCM encrypted payload, which includes the authentication tag.
- `format_version`: The version of the Additional Authenticated Data (AAD) structure used.

By centralizing encrypted payloads in `Envelope`, we enforce consistent cryptographic boundaries and allow for future key rotation or format upgrades seamlessly.

## Additional Authenticated Data (AAD) Strategy
CipherGate utilizes AES-256-GCM, an Authenticated Encryption with Associated Data (AEAD) cipher. AAD is used to cryptographically bind the ciphertext to its intended context, preventing "ciphertext swapping" attacks where a valid ciphertext is moved to another record.

For **Notes**:
- AAD consists of: `version || user_id || note_id`

For **Documents**, we encrypt metadata and content separately:
- Metadata AAD: `version || user_id || document_id || 'metadata'`
- Content AAD: `version || user_id || document_id || 'content'`

This ensures that not only is the data bound to the specific user and document, but a metadata ciphertext cannot be swapped with a content ciphertext.

## Security Experiments
The `Security Lab` module in the frontend interfaces with the `/api/experiments` backend endpoints to demonstrate these security controls in action:
- **Argon2id Memory Hardness (`/bruteforce`)**: Evaluates the cost of hashing to demonstrate resistance against offline cracking.
- **Constant-Time Comparisons (`/timing`)**: Proves that valid and invalid JWT signature comparisons do not leak timing information.
- **AES-GCM Authenticated Fuzzing (`/fuzz`)**: Shows how the system safely rejects any tampering (nonce alteration, ciphertext truncation, AAD mismatch) with an `InvalidTag` exception.
