---
why:
  - site-agnostic-capture
---

# In-Flow Termination

The human operator ends the capture without leaving the browsing flow,
no matter where the session has wandered. Real sessions traverse login
redirects, 2FA pages, and multi-step navigation before reaching the
target content; the completion control must remain available and
functional at every point, or the human has no way to say "done."

Closing the browser window also ends the capture — distinguishably, as
a cancel rather than a success.

**Verification:** Navigate away from the initial page and back; the
completion control remains usable throughout, and activating it ends
the capture successfully. Closing the window instead ends the capture
as a cancel.
