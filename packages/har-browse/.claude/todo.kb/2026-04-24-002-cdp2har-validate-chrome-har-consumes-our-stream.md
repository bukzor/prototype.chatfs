---
anthropic-skill-ownership: llm-subtask
required-reading:
  - packages/har-browse/src/capture.mjs
  - packages/har-browse/.claude/todo.kb/2026-04-24-001-pw-browse-public-events-stream.md
---

# cdp2har: validate chrome-har consumes our stream

**Priority:** High (unblocks the "bonafide HAR on demand" claim)
**Complexity:** Low
**Context:** Capture now emits `{method, params}` JSONL. Claim: `chrome-har`
consumes it unmodified (after `JSON.parse` per line) and emits a valid HAR.
That claim has not been tested end-to-end.

## Problem Statement

We pivoted to CDP passthrough in `{method, params}` shape specifically so
`chrome-har` could consume our stdout. We have not actually run a capture
through `chrome-har` — the claim is structural, not empirical.

## Proposed Solution

Write a tiny wrapper (`src/cdp_to_har.mjs` or shell one-liner) that:

1. Reads JSONL from stdin
2. Parses each line
3. Passes the array to `harFromMessages(messages, {includeTextFromResponseBody: true})`
4. Writes HAR 1.2 JSON to stdout

Smoke-test against the toy server:
`har-browse http://127.0.0.1:8000 | cdp_to_har > toy.har`, then import
into Chrome DevTools → Network → Import HAR to visually verify entries,
timings, bodies, pages.

## Implementation Steps

- [ ] `pnpm add chrome-har` (check latest version; 1.2.1 as of 2026-04-24)
- [ ] Write `src/cdp_to_har.mjs` (~20 lines)
- [ ] Smoke test against toy server; import into DevTools
- [ ] Verify: entries present, bodies populated, timings non-zero, pages
      array populated
- [ ] Add a test (`test_e2e_har.mjs`?) that captures against example.com
      headless, converts, and asserts HAR shape

## Open Questions

- **Body attachment point**: confirm chrome-har reads body from
  `params.response.body` on `Network.responseReceived` (not only from the
  older `Network.requestIntercepted` path shown in the README). Source
  dive if smoke test fails.
- **Missing ExtraInfo events**: we pass `Network.requestWillBeSentExtraInfo`
  and `Network.responseReceivedExtraInfo` through verbatim. Chrome-har
  should handle merging; verify.
- **Redirect chains**: our stream carries `redirectResponse` on
  subsequent `requestWillBeSent` events. Chrome-har should unfold these
  into separate HAR entries; verify visually.

## Success Criteria

- [ ] `cdp_to_har` is a ~20-line pass-through to `harFromMessages`
- [ ] Resulting HAR imports cleanly into Chrome DevTools
- [ ] Entries for `/`, `/index.css`, `/index.js`, `/api/conversation`
      present with bodies and non-zero timings
- [ ] `log.pages[]` has the main navigation with `pageTimings`
