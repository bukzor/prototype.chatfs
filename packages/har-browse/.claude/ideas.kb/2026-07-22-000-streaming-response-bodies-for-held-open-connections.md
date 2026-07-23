---
managed-by: Skill(llm-subtask)
cost-benefit-sweh:
  timebox:
    "@value": 1.0
    rationale: |
      One session: enable Network.streamResourceContent, accumulate
      base64 chunks per requestId from Network.dataReceived, emit at
      LF as today or as accumulated prefix at drain-flush. Plus an SSE
      endpoint in toy_server to test against.
  benefit-2w:
    "@value": 0.7
    rationale: |
      Low for the current chatfs revisit-capture workflow — the
      conversation payload arrives as a plain JSON fetch that completes
      before the human clicks Done, fully covered by the drain and
      clearOriginStorage work (todo.kb 2026-07-22-000/-001). Raised
      2026-07-23 by the abort-based cut (todo.kb 2026-07-23-000):
      requests truncated at the cut now yield headers + abort record
      only, and this is the sole mechanism that preserves their
      pre-cut delivered bytes (the capture-cut-completeness cohort).
      Full value still arrives only if capturing *live* assistant
      responses becomes in-scope: claude.ai and ChatGPT deliver those
      over SSE, and a held-open event stream loses 100% of its data
      under one-shot getResponseBody.
---

# har-browse: streaming response bodies for held-open connections

## The Idea

`Network.getResponseBody` is one-shot and only callable after
`Network.loadingFinished`. A connection still open at capture end — an
SSE/EventSource stream, a long-poll — has no retrievable body at all,
even though client JS consumed every chunk as it arrived. The
abort-based cut (todo.kb `2026-07-23-000-*`, superseding the originally
planned grace-expiry flush) records such a request's headers plus the
browser's abort event, but the body bytes are unrecoverable by that
route.

CDP offers `Network.streamResourceContent`: body chunks then arrive
progressively as base64 in `Network.dataReceived.params.data`.
Accumulate per requestId; at `loadingFinished` emit the canonical body
exactly as today; for a request truncated at the cut, emit the
accumulated prefix alongside its abort record.

Identified 2026-07-22 as gap "D2" in the request-lifetime analysis that
produced the drain-race and IndexedDB-hydration todos; deferred because
the revisit-capture payload is a plain fetch, not a stream.

## Potential Benefits

- Live-streamed assistant responses (SSE) become capturable — the only
  response class the drain/flush work structurally cannot recover.
- Truncated flushes carry the delivered prefix, not just headers —
  strictly more forensic signal.
- Mostly obsoletes buffer-eviction tuning
  (`maxTotalBufferSize`/`maxResourceBufferSize` on `Network.enable`):
  chunks are captured at arrival, not fetched at end.

## Open Questions / Unknowns

- Memory: accumulating every response's chunks in script memory vs.
  only for requests still unfinished (can't know in advance which will
  hang — probably accumulate all, cap per-request).
- Interaction with the BARRIER body-integrity invariants
  (`dev.kb/rust-port.kb/commits.kb/1050-causal-watermark.md`) — a
  prefix-emitted body is a new kind of witness.
- Does the rust-port charter subsume this? If the port lands first, do
  it there instead (chromiumoxide makes it equally natural).

## Exploration Notes

The 2026-07-22 a59dc891 capture holds a live EventSource
(`mcp/v2/bootstrap`) — a ready-made real-world probe. Emitting its
accumulated prefix at flush is the acceptance demo.

## Next Steps (if pursuing)

- [ ] SSE endpoint in `toy_server` (chunked, never-closing)
- [ ] Enable `Network.streamResourceContent`; accumulate
      `dataReceived.params.data` per requestId
- [ ] Wire accumulated prefix into the abort-cut truncation path
      (todo.kb `2026-07-23-000-*`)
- [ ] Mutation entries + tests per `Skill(mutation-testing)`

## Lifecycle

**Status:** Exploring — promote when live-response capture (not just
revisit browsing) enters chatfs scope, when the rust-port charter takes
it up, or if truncation-record fidelity proves insufficient once the
abort-based cut (todo.kb `2026-07-23-000-*`) lands. That todo is this
idea's natural landing site: it names this as its fidelity companion.
