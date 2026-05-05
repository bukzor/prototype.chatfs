# Captured vs Derived

Inside `.chat/$UUID/`, contents split by lifecycle:

- **Captured.** `meta.json`, `conversation.json`, `cdp.jsonl`. Written
  by browse stages directly from provider data. Expensive to regenerate
  (requires Chromium).
- **Derived.** `chat.md`, `messages/`, `conversations/`. Written by
  render stages from captured state. Cheap to regenerate.

## Allowlist captured, purge the rest

Path-render's pre-cleanup inverts the obvious enumeration: instead of
listing derived state to delete, it lists captured state to *keep* and
purges everything else.

```python
CAPTURED = {"meta.json", "conversation.json", "cdp.jsonl"}
for child in chat_dir.iterdir():
    if child.name not in CAPTURED:
        rm child
```

New derived outputs (if `chatgpt-splat` ever adds an `indices/` dir)
require no path-render change — they get cleaned implicitly.

The inversion costs nothing because the captured set is small (3 files)
and stable; the derived set is whatever the splat tool happens to emit
this build. Coupling the cleanup logic to the smaller, more stable set
is correct.
