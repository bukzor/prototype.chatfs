---
why:
  - canonical-conversation-graph
---

# On-Disk Representation: "Rotate 90 Degrees"

The splat format (see `packages/bukzor.chatgpt-export/lib/bukzor/chatgpt_export/splat.py`)
uses a "rotated" layout where:

- **Linear chains -> flat siblings.** Sequential messages are symlinks in the
  same directory, ordered by `{seq:03d}.{role}.{content_type}`.
- **Forks -> subdirectories.** When a message has multiple children, each child
  becomes a subdirectory named `{seq}.{role}.{content_type}.{timestamp}/`.
  The linear chain continues as flat siblings inside each fork directory.
- **Symlinks** point into a deduplicated `messages/` directory (one copy of
  each message's `.json` and `.md`).

Concrete example (a conversation that forks at message 116 into two branches):
```
conversations/
  095.user.text.md -> ../messages/...
  ...                                  # linear: flat siblings
  115.assistant.text.md -> ../messages/...
  116.user.text.2026-03-04T21:39:13/   # fork branch A
    116.user.text.md -> ...
    120.assistant.text.md -> ...
  116.user.text.2026-03-04T21:39:56/   # fork branch B
    116.user.text.md -> ...
    ...                              # linear continues
    134.user.text.2026-...T21:53:22/ # nested fork (3-way)
    134.user.text.2026-...T21:53:32/
    134.user.text.2026-...T21:54:50/
```

Key properties:
- No unnecessary nesting for linear conversation — flat until a fork occurs
- Fork directories are self-describing (who forked, when)
- The pattern recurses naturally for fork-of-fork
- Standard Unix tools work: `ls` shows structure, `find` traverses, `grep -r`
  searches all branches
