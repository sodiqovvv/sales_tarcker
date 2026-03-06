## 2025-05-22 - Path Traversal in File Deletion
**Vulnerability:** Path Traversal
**Learning:** File paths retrieved from external storage (like Firestore) should never be trusted when performing filesystem operations. Using string concatenation like `"app" + rasm` for deletions allows an attacker to manipulate the database record to point to arbitrary system files.
**Prevention:** Always sanitize paths from external sources using `os.path.basename()` to strip directory components and join the result with a trusted base directory using `os.path.join()`. Use `os.path.isfile()` to ensure only files (and not directories) are targeted for deletion.
