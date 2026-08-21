---
why:
  - ../020-goals.kb/safe-automation.md
  - no-network-on-read.md
---

# Explicit Sync Triggers

Refresh is always a deliberate, user-initiated action — never a side effect
of reading. The user must perform an explicit operation (touch, control file
write, CLI command) to trigger network activity.

**Verification:** No combination of filesystem reads causes network traffic.
Only explicit sync commands do.
