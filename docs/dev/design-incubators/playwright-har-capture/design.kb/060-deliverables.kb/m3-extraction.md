---
why:
  - toy-pluck
  - content-encoding-handling
---

# M3 — Extraction

Plucker reliably extracts `/api/conversation` response from HAR.

## Acceptance

- `toy_pluck.sh < out.har > extracted.json` produces correct conversation graph
- Handles HAR-level base64 encoding (Playwright handles HTTP-level compression)
- Handles multiple matching HAR entries (emits all matches)
