# Devlog: 2026-07-22 — har-browse Done-Capturing drain race fix

## Focus

Picked up via `/session-start`: a prior same-day session had committed a
first-cut analysis (`9be5a8a`, then a refinement `4650877`) of two real
har-browse bugs behind the long-standing "wait until `has_more=false`"
flakiness, with fixes sketched but not implemented. Goal was to
implement fixes 1+2 of the Done-Capturing drain race
(`packages/har-browse/.claude/todo.kb/2026-07-22-000-*`): requests still
in flight (sent but not yet `loadingFinished`/`loadingFailed`) at "Done
Capturing" click time were dropped with zero trace, because `inFlight`
only ever tracked post-`loadingFinished` body-fetch promises.

## Decisions

### Separate `pendingInFlight` set, not a shared `inFlight`

**Rationale:** The original sketch (written by the prior session) called
for tracking every sent request via the existing `track()`/`inFlight`
plumbing. Implementing it that way broke `barrier_consumed.spec.mjs`'s
adversarial test: BARRIER's deferred-emit mechanism snapshots `inFlight`
to wait out active body-fetches so consumed RRs land before the BARRIER
that names them — a narrow, fast-resolving set by design. Once
`inFlight` also contained every pending (not-yet-finished) request, a
500-request adversarial-capture BARRIER started waiting on ~495
unrelated, still-outstanding requests, blew past the 2s `drainGraceMs`,
and was silently dropped when `emit("end")` fired first (test failure:
"BARRIER emitted exactly once, Received: 0").

Fix: `pendingRequests`' tracked promises live in a new `pendingInFlight`
Set. The final drain (`done.finally`) waits on the union of `inFlight`
and `pendingInFlight`; BARRIER's `onBindingCalled` keeps waiting on
`inFlight` alone, unchanged from before this session.

**Alternatives considered:** Widening `drainGraceMs` to accommodate slow
BARRIER settling was rejected — it would only mask the same failure mode
at a larger scale (a real capture with hundreds of genuinely slow
requests would still blow the budget), and defeats the point of a
*bounded* drain.

### `drainGraceMs` as an injectable `startCapture` option

**Rationale:** Tests need to pin the grace period (huge, to prove
prompt-end isn't just luck; short, to bound a hung-request test's
runtime) rather than depend on the real 2000ms default. Threaded through
`attachCapture`'s opts and `startCapture`'s opts, defaulting to a
module-level `DRAIN_GRACE_MS = 2000` constant.

## Conventions Established

- Mutation-testing burn-down: for each pre-filed `status: todo` entry,
  inject the diff in `## Injection`, run the targeted spec, confirm red
  with a useful message, revert, confirm green — then flip `status:
  done` and add a one-line confirmation under `## Test Coverage`
  pointing at the actual test name. Applied to the 7 fix-1/2-scoped
  entries; fix-3-scoped and bug-001-scoped (`clearOriginStorage`)
  entries left `status: todo`.
- A test that always overrides an injectable constant (e.g.
  `drainGraceMs`) can never catch a regression to that constant's
  *default* value — `drain-grace-period-zeroed.md` escaped the first
  three tests entirely until a fourth test was added that omits the
  override and exercises the real default.
- Test fixture hygiene: a toy HTTP server with a route that deliberately
  never responds (`/hang`) breaks `server.close()`, which waits for open
  connections to end. Fixed by tracking sockets via the `connection`
  event and destroying stragglers in `close()`.

## Open Questions

- `has_more=false` discriminator (todo.kb 2026-07-22-000's first step)
  remains blocked: the only local claude capture (`a59dc891`) is a
  single-conversation capture with an empty `index-pages.jsonl` — it
  confirms the drain race (2 dropped `api/directory/servers` requests)
  and the cache-hydration bug (zero conversation rWBS) but has no
  index-page data to discriminate the `has_more=false` symptom
  specifically. Needs a fresh live capture reproducing that symptom —
  ask-first, not run this session.
- Fix 3 (flush stashed RRs with a truncation marker at grace expiry) and
  its regression test are still open, along with the live-capture
  validation step (Success Criteria in the todo.kb file).
- `DRAIN_GRACE_MS`'s default value (2000ms) is still an unvalidated
  guess, as noted in the todo.kb file's Open Questions before this
  session.

## References

- `packages/har-browse/.claude/todo.kb/2026-07-22-000-Done-Capturing-race-drops-in-flight-requests-with-no-drain.md`
- `packages/har-browse/tests/inflight_drain.spec.mjs`
- Commits `b571e99` (the fix), `4650877`/`9be5a8a` (prior session's analysis)
