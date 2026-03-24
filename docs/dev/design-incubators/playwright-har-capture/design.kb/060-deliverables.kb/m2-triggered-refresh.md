---
why:
  - toy-capture
  - har-lifecycle
---

# M2 — Triggered Refresh

Capture script injects a "done" button into the target page. Human clicks it
to signal capture is complete. HAR is finalized with traffic from the page's
natural behavior. This proves the capture script can inject controls into
pages it doesn't own.

## Acceptance

- Capture script injects a button into the page (not present in toy server HTML)
- Human clicks the injected button to finalize capture
- HAR contains at least one `/api/conversation` entry (from initial page load)
- Script waits for the button click before closing the context
