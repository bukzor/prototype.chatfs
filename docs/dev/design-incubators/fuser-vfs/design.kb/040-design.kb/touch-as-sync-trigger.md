---
why:
  - no-work-on-read
---

# touch as Sync Trigger

`touch` maps naturally to "create/update cached representation":

| Unix meaning       | chatfs meaning                 |
|-------------------|-------------------------------|
| ensure file exists | ensure conversation is cached |
| update timestamp   | refresh capture               |
| create if missing  | first-time import             |

**FUSE implementation:** Handle in `create()` (if file doesn't exist) or
`utimens()` (timestamp update). Treat as "sync this conversation" — enqueue
BB1→BB2→BB3 pipeline.

**UX benefits:**
- Native to shell tools (`make`, `find`)
- `touch conversations/abc123.md` — ensure/refresh single conversation
- `find chatgpt -name '*.md' -exec touch {} +` — bulk refresh
- Integrates with Makefiles for dependency-driven refresh

**Caveat:** Some editors call `utimens()` automatically when saving. If files
are read-only, this won't cause surprises. Use `touch -c` to avoid accidental
creation.

**Prior art:** sysfs (`echo 1 > /sys/bus/pci/rescan`), procfs
(`echo b > /proc/sysrq-trigger`), systemd (`touch /run/systemd/reload`).
Writes cause work, reads observe results.
