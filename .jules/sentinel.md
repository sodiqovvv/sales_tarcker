## 2025-05-15 - Missing Authentication on Core Endpoints
**Vulnerability:** The application had no authentication or authorization on its core functional endpoints (e.g., product management and sales) despite having the necessary infrastructure for it (JWT, password hashing, etc.).
**Learning:** Even if authentication logic is present in the codebase, it is not effective unless explicitly applied to all sensitive routes. In a multi-user environment, missing authentication allows any unauthenticated user to perform administrative actions.
**Prevention:** Always verify that all sensitive routes are protected by an authentication layer. Use automated security scans or manual audits to ensure that no critical endpoints are left exposed.
