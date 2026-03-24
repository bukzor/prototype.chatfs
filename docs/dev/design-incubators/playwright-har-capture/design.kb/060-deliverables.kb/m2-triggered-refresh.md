---
why:
  - toy-capture
  - har-lifecycle
---

# M2 — Triggered Refresh

Capture script injects a button into the target page and clicks it to trigger
additional network activity. HAR includes multiple transactions for the same
endpoints. This proves the capture script can drive pages it doesn't own.

## Acceptance

- Capture script injects a button into the page (not present in toy server HTML)
- Injected button triggers a fetch to `/api/conversation` when clicked
- HAR contains at least two `/api/conversation` entries (initial load + injected click)
- Script correctly waits for network idle after the triggered action
