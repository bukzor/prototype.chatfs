---
why:
  - explicit-sync-triggers
  - no-network-on-read
source:
  - conversations.cleaned/04-system-decomposition-sync-design/133.assistant.text.md
---

# Sync Control Plane (Procfs/Sysfs Style)

Sync is triggered through control files, never through reads. Three primitives:

```
/provider/
    conversations/...
    control         # write-only: echo sync <id> > control
    status          # read-only: idle | syncing | waiting_user | failed | done
    needs_sync/     # read-only dir: lists stale/missing conversation IDs
```

**Per-conversation hint files:**
- `.sync` or `.SYNC` — reading prints what's stale + exact command to run
- Feels "very Unixy" — instructions as files

**Prior art surveyed:**
- `/sys/block/.../scan`, `/sys/bus/.../rescan` (sysfs control files)
- `/sys/power/state` (write-to-trigger)
- `/proc/sysrq-trigger` (trigger then read result)
- borgfs/restic/rclone mounts (refresh via separate CLI)
- sshfs (separates filesystem view from connection control)

**Why not trigger on read():**
- `grep -r` triggers dozens of syncs
- Editors stat/read files unexpectedly
- Shell completions cause side effects
- Tools may read files repeatedly
- Kernel interfaces strongly avoid side effects on `read()` for this reason

**Status file states:** `idle`, `syncing`, `waiting_for_user`, `failed`, `done`,
`last_sync=<timestamp>`. Useful for the browser-driven capture step where
user interaction is required.
