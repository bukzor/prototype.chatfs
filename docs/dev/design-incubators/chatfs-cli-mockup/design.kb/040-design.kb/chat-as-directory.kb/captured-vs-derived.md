# Captured vs Derived

Inside `.chat/$UUID/`, contents split by lifecycle:

- **Captured.** `meta.json`, `conversation.json`, `cdp.jsonl`. Written
  by browse stages directly from provider data. Expensive to regenerate
  (requires Chromium). Quarantined under `.chat/$UUID/.data/`.
- **Derived.** `chat.md`, `messages/`, `conversations/`. Written by
  render stages from captured state. Cheap to regenerate. Live at
  chat-dir root — they're the user surface.

```
.chat/$UUID/
    chat.md          # derived
    messages/        # derived
    conversations/   # derived
    .data/           # captured (hidden from default ls)
        meta.json
        conversation.json
        cdp.jsonl
```

## Allowlist `.data/`, purge the rest

Path-render's pre-cleanup keeps the captured *directory* and purges
everything else at the chat-dir root:

```python
KEEP = {".data"}
for child in chat_dir.iterdir():
    if child.name not in KEEP:
        rm child
```

The allowlist is one entry, not three. New derived outputs (if
`chatgpt-splat` ever adds an `indices/` dir) require no path-render
change — they get cleaned implicitly.

The dot-prefix has two jobs:

1. **Hidden from default `ls`.** The user-visible chat surface is
   `chat.md`, `messages/`, `conversations/` — what they came for.
   `ls -a` reveals `.data/` for inspection.
2. **Reachable through the view symlink.** `view/$TITLE/.data/meta.json`
   resolves to `.chat/$UUID/.data/meta.json`. Captured artifacts stay
   addressable for debugging, just out of the way for normal browsing.

Coupling the cleanup logic to the captured set is correct because that
set is small and stable; the derived set is whatever the splat tool
happens to emit this build.
