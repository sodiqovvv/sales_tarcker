## 2025-03-14 - Path Traversal in File Deletion and Stored XSS via SVG Uploads

**Vulnerability:** The `ochirish` endpoint was vulnerable to path traversal because it used raw strings from the database (e.g., `/static/uploads/file.png`) to construct deletion paths without sanitization. An attacker could potentially delete arbitrary files if they could manipulate the database record. Additionally, the `mahsulot_qoshish` endpoint allowed arbitrary file uploads, which could include malicious SVG files containing JavaScript (Stored XSS).

**Learning:** Database-derived file paths should be treated as untrusted, especially when used in filesystem operations. Sanitizing with `os.path.basename()` is a simple yet effective defense. SVG files, while technically images, are XML documents that can execute scripts in the browser, making them a common vector for XSS in upload forms.

**Prevention:**
1. Always use `os.path.basename()` when using stored paths for file operations.
2. Restrict file deletions to specific, trusted directories.
3. Use strict allowlists for file extensions and content types for uploads; specifically exclude SVG if not strictly necessary and properly sanitized.
4. Enforce environment-specific secrets (like `SECRET_KEY`) by failing at startup if they are missing or insecure.
