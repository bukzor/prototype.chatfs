---
status: done
---

# `har_browse.mjs`: EPIPE break replaced with continue

The `if (stdoutClosed) break;` guard exits the event loop once the
downstream consumer (e.g. `head -n 1`, `jq | limit`) closes the pipe.
Replace `break` with `continue` and the loop spins forever consuming
events that can't be delivered — the process never terminates after
EPIPE, the browser stays open, and the test wrapper has to SIGTERM the
process group.

## Injection

`src/har_browse.mjs`:

```diff
-    if (stdoutClosed) break;
+    if (stdoutClosed) continue;
```

## Test Coverage

`tests/epipe.test.mjs` — "har-browse | head -n 1 exits cleanly". With
`continue`, the loop never terminates; `timeout 15s` SIGTERMs the
process group and `exec` exits with code 124 (test failure). Green
case ~2s.
