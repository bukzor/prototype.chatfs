---
status: done
---

# `har_browse.mjs`: `JSON.stringify(ev, null, 2)` breaks JSONL

JSONL is one JSON value per line. `JSON.stringify(ev, null, 2)` emits
indented multi-line JSON; each event spans many lines, and downstream
line-oriented consumers (`jq -c`, `cdp_to_har`'s readline loop) parse
fragments as separate documents and fail.

## Injection

`src/har_browse.mjs`:

```diff
-    process.stdout.write(JSON.stringify(ev) + "\n");
+    process.stdout.write(JSON.stringify(ev, null, 2) + "\n");
```

## Test Coverage

`tests/epipe.test.mjs` — `head -n 1` yields just `{` (the opening
brace of the first pretty-printed object). The test's
`JSON.parse(stdout.trim())` throws on the bare brace and the test
fails at `tests/epipe.test.mjs:61`.
