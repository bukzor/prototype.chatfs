---
why:
  - safe-automation
  - no-network-on-read
---

# Explicit Sync Triggers

Refresh is always a deliberate, user-initiated action — never a side effect
of reading. The user must perform an explicit operation (touch, control file
write, CLI command) to trigger network activity.

**Verification:** No combination of filesystem reads causes network traffic.
Only explicit sync commands do.
