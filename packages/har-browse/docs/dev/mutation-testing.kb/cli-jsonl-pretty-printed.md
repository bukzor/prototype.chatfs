---
status: todo
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

## Hypothesis

`tests/epipe.test.mjs` ("har-browse | head -n 1 exits cleanly") may
already catch this: with `JSON.stringify(ev, null, 2)`, `head -n 1`
yields just `{` (the opening brace of the first object), and the
test's `JSON.parse(stdout.trim())` throws. Drive through
inject→test→revert to confirm and link.
