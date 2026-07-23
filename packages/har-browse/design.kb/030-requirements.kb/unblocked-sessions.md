---
why:
  - site-agnostic-capture
---

# Unblocked Sessions

Target sites treat a capture session like ordinary browsing. The
instrumentation must not make the session more suspicious to bot
detection (TLS fingerprint, UA anomalies, automation tells) than the
same human in an uninstrumented browser — a blocked or challenged
session yields no data at all.

Deliberate self-identification (a tool-identifying User-Agent suffix)
is policy, not leakage: identify honestly while remaining a real
browser in every way the site can measure.

**Verification:** A capture session against a bot-protected production
site proceeds with no challenges beyond those the same profile
receives uninstrumented.
