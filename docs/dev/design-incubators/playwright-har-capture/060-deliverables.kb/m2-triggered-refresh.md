---
why:
  - toy-capture
  - har-lifecycle
---

# M2 — Triggered Refresh

Capture script triggers the in-page "refresh conversation" button. HAR includes
multiple transactions for the same endpoints.

## Acceptance

- HAR contains at least two `/api/conversation` entries (initial load + refresh)
- Script correctly waits for network idle after the triggered action
