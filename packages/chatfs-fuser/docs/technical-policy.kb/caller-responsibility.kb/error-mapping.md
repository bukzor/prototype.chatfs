---
why:
  - posix-error-semantics
source:
  - design-session (2026-03-20)
---

# Error Mapping

The framework translates resolution failures to POSIX errnos (ENOENT, ESTALE,
ENOTDIR, EISDIR). Caller callbacks are not expected to return error types —
they return data or nothing. The framework detects missing entries during path
resolution and maps to the appropriate errno.

Callers who need custom error behavior (e.g. returning empty content instead
of ENOENT) handle it in their callbacks.
