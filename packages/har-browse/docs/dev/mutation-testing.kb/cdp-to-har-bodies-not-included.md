---
status: done
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

## Test Coverage

`tests/cdp_to_har.test.mjs` — "cdp-to-har includes response body
text in HAR entries". Spawns the CLI with a hand-crafted minimal CDP
sequence (Page.frameStartedLoading + Network.{requestWillBeSent,
responseReceived with body, loadingFinished}) and asserts
`entry.response.content.text` equals the seeded body. With the option
dropped, `text` is `undefined` and `assert.equal` fails.
