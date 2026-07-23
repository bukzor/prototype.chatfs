---
why:
  - data-possession
---

# Crash Durability

Captured data survives abnormal termination. If the browser, the
capture process, or the machine dies mid-session, everything captured
up to the failure — except at most the record in flight — is already
out of the capture's hands, well-formed, and usable.

A human capture session is long and unrepeatable (logins, 2FA, the
operator's time); losing forty minutes of capture to a crash at minute
forty is a mission failure, not an inconvenience.

**Verification:** `kill -9` the capture mid-session; the output so far
is parseable and contains every record emitted before the kill.
