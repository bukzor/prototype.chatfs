---
status: done
---

# `capture.mjs`: base64 encoding flag not set on RR

When `Network.getResponseBody` returns `base64Encoded: true` (binary
bodies), we must set `rr.response.encoding = "base64"` so chrome-har
preserves the encoding marker in HAR output. Dropping the flag makes
downstream consumers treat the base64 text as UTF-8 — silently
corrupts every image, font, and gzipped body in the capture.

## Injection

`src/capture.mjs`, in `onLoadingFinished`:

```diff
           rr.response.body = body.body;
-          if (body.base64Encoded) rr.response.encoding = "base64";
```

## Test Coverage

`tests/har.spec.mjs`: "startCapture → chrome-har produces usable HAR"
fails when this is dropped. Some response served by the toy server
arrives base64-encoded from CDP; without the encoding flag the
downstream HAR builder treats the base64 text as UTF-8 and the JSON
parse in the test fails.
