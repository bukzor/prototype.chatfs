---
status: todo
---

# `cdp_to_har.mjs`: empty-line skip dropped

The readline loop's `if (!line.trim()) continue` tolerates blank lines
in the JSONL input (trailing newline from `> events.jsonl`,
shell-pipeline EOF artifact, accidental double-newline). Drop it and
`JSON.parse("")` throws `SyntaxError: Unexpected end of JSON input` —
the whole pipeline fails on the most benign input quirk.

## Injection

`src/cdp_to_har.mjs`:

```diff
 for await (const line of rl) {
-  if (!line.trim()) continue;
   messages.push(JSON.parse(line));
 }
```

## Fixture needed

Unit test (new `src/cdp_to_har.test.mjs` or
`tests/cdp_to_har.test.mjs`): pipe `"\n"` (or valid JSONL with a
trailing blank line) into `cdp_to_har`, assert exit 0 and HAR JSON on
stdout. Without the skip, exit is non-zero with a SyntaxError on
stderr.
