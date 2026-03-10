## 2025-05-15 - [Authentication Bypass]
**Vulnerability:** Core application endpoints (index, add product, sell, delete) are missing authentication checks, even though the application has login/register templates and an `auth.py` module.
**Learning:** The implementation of authentication was completely omitted from the main application logic, despite the supporting infrastructure being present.
**Prevention:** Always verify that a `get_current_user` or similar dependency is applied to all protected routes.
