# Debugging Log

**Date:** 30 September 2026

### Incident 1: 401 Handling Incorrectly Logs Out Tampering Demo
- **Symptom:** When tampered tokens were sent via the API playground, the app's `window.dispatchEvent(new Event("auth-expired"))` logged the user out, closing the active playground session unexpectedly.
- **Root Cause:** A generic 401 response interceptor in `api/client.ts` cleared local tokens regardless of whether the token being tested was the real session token or a specifically tampered mock token.
- **Fix:** Updated the `api()` function to accept a `tokenOverride` argument. The 401 interceptor now checks if `tokenOverride === undefined` before dispatching `auth-expired`.
- **Regression Test / Prevention:** The `test_ciphertext_tampering_is_rejected` explicitly tests the backend mechanism without requiring the frontend. The frontend was manually verified by tampering a token and ensuring the session remained active.

### Incident 2: Nonce Re-use on Update
- **Symptom:** Updating a note failed with `IntegrityError` on the `uq_notes_key_id_nonce` constraint in tests.
- **Root Cause:** Early draft code reused the original nonce when re-encrypting the updated note payload.
- **Fix:** Ensured a fresh `secrets.token_bytes(12)` is generated inside `encrypt_note` on every update, as mandated by the guide. Wrapped the DB commit in a retry loop (up to 3 times) for the extreme edge case of a nonce collision.
- **Regression Test / Prevention:** `test_crud_notes` performs an update. An automated test verifying different nonces across saves would catch this regression.
