## 2025-05-14 - Path Traversal in File Deletion
**Vulnerability:** The `ochirish` endpoint deleted files using paths directly from the database without sanitization, allowing for arbitrary file deletion via path traversal (`../../`).
**Learning:** Even internal database-driven paths should be treated as untrusted if they can be influenced by users or if the system should be resilient to database compromise.
**Prevention:** Use `os.path.basename()` to extract only the filename and join it with a trusted base directory. Verify the existence and location of the file before deletion.

## 2025-05-14 - Stored XSS via SVG Upload
**Vulnerability:** Lack of file type validation allowed uploading SVG files, which can contain malicious XML/JavaScript payloads for XSS.
**Learning:** Relying on simple file extension checks is insufficient; explicit rejection of SVG and validation of both extension and Content-Type are necessary.
**Prevention:** Implement strict allow-lists for image extensions and validate that the Content-Type matches. Explicitly block `image/svg+xml`.
