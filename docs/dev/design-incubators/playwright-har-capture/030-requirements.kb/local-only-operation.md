---
why:
  - safe-learning-environment
---

# Local-Only Operation

The toy backend runs on 127.0.0.1 with no authentication. No network requests
leave the machine. The Playwright script targets only this local server.

**Verification:** `tcpdump` or equivalent shows zero external traffic during a
full capture run.
