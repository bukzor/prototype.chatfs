---
status: done
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

## Test Coverage

`tests/cdp_to_har.test.mjs` — "cdp-to-har tolerates blank lines in
JSONL input". Pipes the valid fixture with extra blank lines injected
mid-stream and at EOF; asserts exit 0 and parseable HAR on stdout.
Without the skip, `JSON.parse("")` throws and the CLI exits non-zero.
