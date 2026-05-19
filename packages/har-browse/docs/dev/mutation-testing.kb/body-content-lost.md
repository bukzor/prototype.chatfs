---
status: done
---

# `capture.mjs`: response body content overwritten with empty string

The whole point of the body-fetch dance is that `Network.getResponseBody` returns the bytes and we attach them to the
already-stashed RR. If the assignment writes `""` instead of
`body.body`, RR still emits in correct order with the base64 flag
set, but every body is empty.

## Injection

`src/capture.mjs`, in `onLoadingFinished`:

```diff
-          rr.response.body = body.body;
+          rr.response.body = "";
```

## Test Coverage

`tests/har.spec.mjs`: "startCapture → chrome-har produces usable HAR"
asserts `api.response.content.text` JSON-parses and exposes
`messages`. Empty body means `JSON.parse("")` throws or
`Object.keys({}).length === 0` — equality check on
`>= 1 messages` fails.
