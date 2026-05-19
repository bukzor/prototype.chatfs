---
status: done
---

# `har_browse.mjs`: trailing `\n` dropped from JSONL writes

`process.stdout.write(JSON.stringify(ev) + "\n")` is what makes the
output line-delimited. Drop the `+ "\n"` and the entire capture lands
as one giant JSON-object-concatenation blob — unparseable by any JSONL
consumer (`jq -c`, `cdp_to_har`, the toy_pluck.sh filter, etc.).

## Injection

`src/har_browse.mjs`:

```diff
-    process.stdout.write(JSON.stringify(ev) + "\n");
+    process.stdout.write(JSON.stringify(ev));
```

## Test Coverage

`tests/epipe.test.mjs` — "har-browse | head -n 1 exits cleanly". With
no newline, `head -n 1` waits forever; the outer `timeout(1)` wrapper
fires SIGTERM at 15s on the whole process group (Chromium included)
and the test fails with exit code 124. The same wrapper leaves the
green case at ~2s.

While here, also tightened the test infra: replaced the prior Node-side
`exec` timeout (which couldn't reach Chromium descendants when sh died)
with GNU `timeout 15s sh -c '...'` — by default it puts the command in
a fresh process group and SIGTERMs the group, so a misbehaving
har-browse tears down with Chromium rather than leaving an orphan
window the user has to close manually. SIGTERM only — Chromium handles
it cleanly, no SIGKILL fallback needed.
