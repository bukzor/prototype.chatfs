---
status: todo
---

# `cdp_to_har.mjs`: `includeTextFromResponseBody` option dropped

The whole point of attaching `body` to `Network.responseReceived.params.response`
is that `chrome-har` will lift it into `entries[].response.content.text` —
but only when `includeTextFromResponseBody: true` is passed. Drop the
option and bodies stop appearing in HAR output even though the capture
side did its job.

## Injection

`src/cdp_to_har.mjs`:

```diff
-const har = await harFromMessages(messages, {
-  includeTextFromResponseBody: true,
-});
+const har = await harFromMessages(messages);
```

## Fixture needed

No existing test exercises the `cdp_to_har.mjs` CLI binary —
`tests/har.spec.mjs` imports `harFromMessages` directly. Need a CLI
integration test (spawn `cdp-to-har` as a subprocess like
`tests/epipe.test.mjs` does for `har-browse`): pipe a known
`{method, params}` stream that includes a `Network.responseReceived`
with `response.body`, then assert the HAR JSON on stdout has
`entries[].response.content.text` populated. Without the option, `text`
is absent (or empty).
