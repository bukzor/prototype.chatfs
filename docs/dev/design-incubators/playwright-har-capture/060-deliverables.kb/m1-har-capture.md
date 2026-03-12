---
why:
  - toy-capture
  - har-lifecycle
---

# M1 — HAR Capture

Playwright captures a HAR for a single page load.

## Acceptance

- `toy_capture --url http://127.0.0.1:8000 --har out.har` produces a valid HAR
- HAR contains entries for `/`, `/api/ping`, `/api/conversation`, `/api/large`
- Script exits 0 on success
