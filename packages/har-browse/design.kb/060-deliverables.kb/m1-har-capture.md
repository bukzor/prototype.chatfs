---
why:
  - toy-capture
  - har-lifecycle
---

# M1 — HAR Capture

Playwright captures a HAR for a single page load.

## Acceptance

- `./src/har_browse.mjs` produces a valid HAR
- HAR contains entries for `/`, `/index.css`, `/index.js`, `/api/conversation`
- Script exits 0 on success
