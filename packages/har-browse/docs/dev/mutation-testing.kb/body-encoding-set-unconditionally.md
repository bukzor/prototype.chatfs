---
status: done
---

# `capture.mjs`: response.encoding set to "base64" without checking flag

`if (body.base64Encoded) rr.response.encoding = "base64";` —  the
guard exists because CDP returns `base64Encoded: false` for textual
bodies (already utf-8 in `body.body`). Drop the `if` and every
response is tagged base64, so chrome-har treats text bodies as base64
and HAR output contains garbled text (decoded-from-base64 nonsense).
Symmetric mutation to `body-base64-flag-dropped` (which drops the
flag in the other direction).

## Injection

`src/capture.mjs` in `onLoadingFinished`:

```diff
-  if (body.base64Encoded) rr.response.encoding = "base64";
+  rr.response.encoding = "base64";
```

## Test Coverage

`tests/body_encoding.spec.mjs` — "text responses are not tagged base64
in capture stream" — fetches `/payload` (text JSON), inspects the raw
captured RR (pre chrome-har), and asserts
`response.encoding !== "base64"`. The toy server's text bodies arrive
with `base64Encoded: false`, so the unconditional mutation mistags
them and the assertion fails fast.

Note: `tests/har.spec.mjs` (which feeds the stream through chrome-har)
tolerates this mutation because chrome-har re-encodes textual bodies
when it sees `encoding=base64` in the input — the bug only surfaces on
the raw RR. `tests/example.spec.mjs` catches it via real-network HTML
body decode, but requires internet.
