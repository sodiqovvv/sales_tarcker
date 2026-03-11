## 2025-05-15 - [Path Traversal in File Deletion]
**Vulnerability:** The application was vulnerable to path traversal because it used unsanitized database-derived file paths directly in `os.path.exists` and `os.remove`.
**Learning:** Database values (like image URLs) should be treated as untrusted if they can be manipulated by users or if they contain relative path components.
**Prevention:** Always use `os.path.basename()` to extract only the filename from stored paths and join it with a trusted base directory. Use `os.path.isfile()` to verify the file exists within that trusted directory before performing deletions.
