---
why:
  - toy-pluck
  - content-encoding-handling
---

# M3 — Extraction

Plucker reliably extracts `/api/conversation` response from HAR.

## Acceptance

- `toy_pluck out.har --out extracted.json` produces correct conversation graph
- Works regardless of content encoding (identity, gzip, brotli)
- Handles multiple matching HAR entries (picks the right one)
