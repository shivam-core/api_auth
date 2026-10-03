# Upgrade Audit & Implementation Plan

## 1. Existing / Missing / Needs-Fix Matrix

| Feature | Status | Notes |
|---|---|---|
| **Passwords and Login** | Existing | Uses Argon2id. Rate limiting is basic. Needs verification for rehash-on-success and proper JWT payload/skew handling. |
| **Access Tokens & Sessions** | Existing / Needs Fix | RS256 JWTs are issued. Needs `/api/sessions` (list), `/api/sessions/revoke-others`. |
| **Notes Encryption** | Existing | Uses AES-256-GCM with proper nonces, AAD, and tags. Needs client-side search. |
| **Documents** | Missing | Needs `Document` model, multipart upload, file validation, quota enforcement, encryption, and download routes. |
| **Overview Dashboard** | Missing | Needs `/api/overview` endpoint and frontend overview page. |
| **Security Events** | Existing / Needs Fix | `AuditEvent` model exists and `/api/audit` exists. Needs to be mapped to `/api/security/events` and frontend built. |
| **Security Lab & Playground** | Missing | Needs `/api/lab/experiments/{name}` runner with 9 specific experiments. Frontend API playground needed. |
| **Inspector & Educational Pages** | Missing | Frontend needs JWT inspector and encryption envelope displays. |
| **Visualizer** | Missing | Needs the "Professional operation visualizer" (drawer, status, traces). |
| **Tests & Verification** | Missing | Needs integration tests meeting A01-A24 acceptance criteria. |

## 2. Migration Strategy
- Make additive schema migrations using Alembic for `documents` table and updating `auth_sessions`/`audit_events` if needed.
- Preserve existing `notes`, `users`, `auth_sessions`, and `audit_events`.
- Keep existing `key_id` references valid.

## 3. Specific Implementation Plan
1. **Backend - Database & Models:** Add `Document` model. Create Alembic migration.
2. **Backend - Services & Security:** Add document encryption (`document_aad`, `encrypt_document`, `decrypt_document`). Implement overview, lab experiments, and complete session routes.
3. **Backend - Routers:** Implement `/api/overview`, `/api/documents/*`, `/api/lab/*`.
4. **Frontend - Core & Visualizer:** Setup layout, theme tokens, and the operation visualizer context/components.
5. **Frontend - Features:** Build Documents, Notes, Sessions, Overview, Lab, and Playground pages.
6. **Testing:** Write backend tests in `backend/tests/` using `pytest`.
7. **Documentation:** Update README and write required docs in `docs/`.
8. **Deployment:** Push to GitHub, observe Render deployment, and verify live URL.
