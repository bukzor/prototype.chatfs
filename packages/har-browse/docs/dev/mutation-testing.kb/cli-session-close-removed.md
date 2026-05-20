---
status: done
---

# `har_browse.mjs`: session.close() removed from finally

The `finally { await session.close(); }` is what tears down the
Chromium context when the iterator ends (Done click, window close,
EPIPE break, throw). Drop the await and the CLI exits but Chromium
descendant processes stay running — an orphan window the user must
close manually, and a leaked profile lock that blocks the next launch.

## Injection

`src/har_browse.mjs`:

```diff
 try {
   for await (const ev of session.events) {
     if (stdoutClosed) break;
     process.stdout.write(JSON.stringify(ev) + "\n");
   }
-} finally {
-  await session.close();
-}
+}
```

## Test Coverage

`tests/epipe.test.mjs` — after `head -n 1` closes the pipe, the loop
breaks and the function returns, but Playwright's CDP websocket keeps
Node alive (event loop pinned). `timeout 5s` fires SIGTERM on the
process group at the 5s mark; `exec` rejects with code 124. Green
case ~1.8s, mutated case ~5.5s.

A buggy-passing variant (`process.exit(0)` after the loop) would
orphan Chromium silently — not currently tested for, but unnatural in
this codebase.
