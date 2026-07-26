# User-Agent system-information comment

**Verdict: shipped.**

A `; `-separated field appended to the User-Agent's first comment:

```
Mozilla/5.0 (X11; Linux x86_64; har-browse/1.0.0; +https://…) \
AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
```

Accepted where the trailing product is refused
(`../ua-position-gate.md`), and reaches every server that reads
`User-Agent` — still nearly all of them.

## What it asserts

The slot conventionally holds OS and CPU, so this claims to be a
property of the environment the browser runs in, rather than another
layer in the user-agent stack. That is what a capture harness actually
is: the browser runs inside us, not through us.

## Cost

A sniffer that indexes the comment's fields positionally could misread
the third one. Low risk — Windows (`Windows NT 10.0; Win64; x64`) and
Android (`Linux; Android 10; K`) ship three and four fields, so parsers
already tolerate more than two.

No client-hint mismatch arises. The comment is not part of the client
hints surface at all, and the consistency signals sites check —
platform, mobile, Chrome major version — are untouched.

That last point is what rules out the `(compatible; har-browse/1.0.0;
+URL)` spelling, which replaces the platform rather than extending it.
It would contradict `Sec-CH-UA-Platform` and
`Sec-CH-UA-Platform-Version` — a real mismatch, where the shipped form
has none — and it is a fabrication rather than a disclosure, failing
`unblocked-sessions`' second half to satisfy its first.

## Implementation

`brandUserAgent()` in `src/host_puppeteer.mjs`. Held by
`tests/brand_user_agent.test.mjs` (ABNF as the oracle) and
`tests/user_agent_client_hints.spec.mjs` (end-to-end: nothing trails the
product list, and the hints survive).
