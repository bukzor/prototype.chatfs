---
why:
  - ../020-goals.kb/site-agnostic-capture.md
---

# Unblocked Sessions

Target sites treat a capture session like ordinary browsing. The
instrumentation must not make the session more suspicious to bot
detection (TLS fingerprint, UA anomalies, automation tells) than the
same human in an uninstrumented browser — a blocked or challenged
session yields no data at all.

Deliberate self-identification is policy, not leakage: identify
honestly while remaining a real browser in every way the site can
measure. Where the disclosure sits is not free choice — providers gate
on its position, and the bot convention of a trailing User-Agent product
is measured-refused. See `040-design.kb/self-identification.kb/`.

**Verification:** A capture session against a bot-protected production
site proceeds with no challenges beyond those the same profile
receives uninstrumented.
