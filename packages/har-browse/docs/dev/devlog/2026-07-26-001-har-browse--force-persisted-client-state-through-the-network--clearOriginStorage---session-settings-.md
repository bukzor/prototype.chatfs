# Devlog: 2026-07-26 — har-browse: force persisted client state through the network (clearOriginStorage + session settings)

## Focus

Implement `.claude/todo.kb/2026-07-22-001-*`: a capture of a claude.ai
revisit contains zero conversation traffic, because the app hydrates
from its persisted React Query IndexedDB cache and never asks the
network for the conversation. Capture cannot recover a response that
never crossed the wire, so the fix is to make the app ask.

Landed: `clearOriginStorage` on `startCapture` (CDP
`Storage.clearDataForOrigin`, `indexeddb,cache_storage`, before
`page.goto`), the `--clear-origin-storage` CLI flag, and two
unconditional per-session settings in `wireSession` --
`Network.setCacheDisabled` and `Network.setBypassServiceWorker`. Six new
tests across `tests/clear_origin_storage.spec.mjs` and
`tests/session_settings.spec.mjs`; six mutation entries in
`docs/dev/mutation-testing.kb/` now `done`, each confirmed red under
injection. `pnpm test` green (28 e2e + units). Not done: live
verification against real providers, which needs a real browser and
login and so waits for the user.

## Decisions

### The wrong-origin mutation's predicted kill was wrong, and the correct test asserts scope

The pre-filed `clear-origin-storage-wrong-origin` entry predicted that
deriving the origin from `page.url()` instead of the target URL would
be caught by the ordinary payload-presence assertion, on the theory
that the target origin's cache would survive and hydration would
proceed. It survived that test instead.

Probing found why: pre-goto the page sits on `about:blank`, whose
origin serializes to `"null"`, and CDP answers a `"null"` origin by
clearing IndexedDB for *every* origin in the profile -- verified
directly by populating a bystander origin and watching a
`"null"`-origin clear wipe it. So in this test the mutant over-clears
rather than under-clears, and the payload still refetches.

It is still a real defect: in production the pre-goto page holds a
restored tab's URL often enough, and then it under-clears the target
while wiping an unrelated site. Either way the defect is scope, so the
new test asserts scope directly -- a second `startServer()` on another
port is populated in the first capture and must still hydrate after the
second capture clears the target origin. That kills the mutant, and it
states the invariant the feature actually promises.

**Alternatives considered:** asserting on the CDP call's arguments via
a fake session. Rejected -- it pins the mechanism rather than the
promise, and would have passed the `"null"`-origin behavior right by.

### Cookie survival is asserted through `requestWillBeSentExtraInfo`, not `requestWillBeSent`

`Network.requestWillBeSent` reports renderer-side headers; the network
service adds cookies afterward, so the `Cookie` header only appears in
`Network.requestWillBeSentExtraInfo`, which carries a `requestId` and
no URL. The test correlates the two by `requestId`. Worth remembering
before writing any other header assertion against this stream.

Also load-bearing in that test: the cookie is set with an expiry,
because a session cookie is not written to the profile on disk and
would not survive the browser restart between the two captures.

### The service-worker test loads three times

`Network.setBypassServiceWorker(true)` leaves the page uncontrolled
(`navigator.serviceWorker.controller` stays null), which is the
mechanism by which its fetches reach the network -- and the reason a
fixture cannot wait for a controller before fetching, as the first
draft did and hung. Three loads make the mutant's kill deterministic:
the first only registers the worker (whether `clients.claim()` lands
before that load's fetch is a race), the second is controlled from the
start and populates the worker's cache, and the third is the load a
cache-first worker could answer entirely off-network. The oracle is the
server's `requestLog`: all three fetches must reach it.

### `--clear-origin-storage` defaults off

The mechanism belongs to har-browse; whether a given capture should
force a refetch is provider policy, and the taskfile's open question on
that is unresolved. Off by default until it is answered.

## Conventions Established

- Server-side `requestLog` is the oracle for "this actually crossed the
  network". Stream assertions can confirm the capture holds a response,
  but only the server can testify that a request was made -- exactly
  the distinction this whole class of bug turns on.
- A fixture that produces the bug regime needs its own control test.
  `clear_origin_storage.spec.mjs` pins `/hydrate` to hydrating-on-revisit
  so the kill assertions cannot quietly become tautologies if the
  fixture stops caching.

## Open Questions

- Does claude.ai's React Query revalidate the persisted entry in the
  background (stale-while-revalidate)? If so, waiting longer before
  Done would also capture the traffic, which bounds how much the clear
  is worth. One observation run answers it.
- Which origins to clear for claude.ai -- the `keyval` database lives
  on `https://claude.ai`, but API/CDN origins are unexamined.
- Should the clear default on for chatfs provider flows (chatfs-side
  policy) rather than staying an opt-in har-browse flag?

## References

- `.claude/todo.kb/2026-07-22-001-claude-ai-revisits-render-from-persisted-React-Query-IndexedDB-cache--so-capture-sees-no-conversation-traffic.md`
- `docs/dev/mutation-testing.kb/clear-origin-storage-*.md`, `session-*.md`
- `.claude/todo.kb/2026-07-23-001-Zero-miss-target-coverage-via-Target-setAutoAttach.md`
  -- the service-worker bypass is that todo's interim mitigation, not
  its replacement: worker-target traffic other than the controlled
  page's own fetches is still invisible.
