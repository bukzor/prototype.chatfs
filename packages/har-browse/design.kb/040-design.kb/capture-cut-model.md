---
why:
  - capture-cut-completeness
---

# Capture Cut Model — Lanes, Gaps, and the Abort-Based Drain

Conceptual model for reasoning about capture completeness. Use this when
a capture is missing data the user saw on screen, or when changing
shutdown/drain behavior.

## The lanes

Data crosses independent lanes on its way to the output, each with its
own buffering and latency:

1. **Physical network** — bytes on the wire
2. **Client JavaScript** — the page renders what arrived
3. **In-page capture JS** — the injected overlay (`src/inject.mjs`);
   registers the Done click
4. **Capture process** — CDP sessions + handlers (`src/capture.mjs`);
   notices the click, runs the drain
5. **stdout** — the JSONL event stream

The Done cut originates in lane 3 (human clicks after lane 2 showed them
what they wanted) and propagates downward with latency. Because a
later-detected cut only *enlarges* the cohort, propagation latency is
benign — see `030-requirements.kb/capture-cut-completeness.md` for the
causality argument.

## Gap taxonomy: how the client can see data the output lacks

Every "the page showed it but the capture doesn't have it" report falls
in one of these classes. Diagnose by grepping the capture for the
datum's `requestWillBeSent` (rWBS):

| Class | Signature | Mechanism | Tracked in |
|---|---|---|---|
| **Never requested** | no rWBS | App hydrated from persisted storage (IndexedDB/React Query, Cache Storage); traffic happened in a *previous* session | `.claude/todo.kb/2026-07-22-001-*` (clear origin storage pre-goto) |
| **Requested, never seen** | no rWBS | Traffic rode a CDP target we hold no session for: service worker, shared worker, OOPIF, prerender — or fired in a popup's pre-`Network.enable` window | `.claude/todo.kb/2026-07-23-001-*` (`Target.setAutoAttach`) |
| **Seen, then dropped** | rWBS without RR | Lifecycle: request unfinished at the cut; internal buffers (`awaitingBody` stash) held its events hostage to a post-cut terminal event | `.claude/todo.kb/2026-07-22-000-*` (landed) + `2026-07-23-000-*` (abort-based cut) |
| **Seen, bytes not in stream** | RR present, body absent/partial | Bodies are only fetchable post-`loadingFinished` (one-shot `getResponseBody`); streamed/held-open responses have no retrievable body; large bodies can be evicted | `.claude/ideas.kb/2026-07-22-000-*` (`Network.streamResourceContent`) |
| **Delivered, then lost in our pipe** | event observed under debugger, absent from output | Events enqueued after `emit("end")` land in a closed queue; stdout flush/EPIPE handling | `.claude/todo.kb/2026-07-23-000-*` (make post-`end` enqueues loud) |

The first two classes are forensically identical (no rWBS) in a per-page
capture — one reason target coverage matters even when no loss is
proven.

## The drain: abort-based cut, not grace period

Shapes the drain has taken, in order:

1. **No drain at all** (pre-2026-07-22): only post-`loadingFinished`
   body fetches were awaited; unfinished cohort requests vanished
   traceless. The invisible loss enabled a root-cause misattribution
   (see todo.kb `2026-07-22-000-*`, Current Situation).
2. **Grace-period drain** (landed 2026-07-22): track every request from
   rWBS to terminal event; wait out stragglers, bounded by
   `drainGraceMs`. Sound, but wrong-shaped: the grace period buys time
   for *post-cut* arrivals — data outside the cohort — and because
   held-open connections (EventSource/long-poll) are normal, every
   capture pays the full grace floor. Timer expiry drops the remainder
   silently.

> [!TODO] Abort-based cut replaces the grace period
> At cut detection, *force* every in-flight request to a terminal event
> by disabling networking, then wait — event-driven — for the pending
> ledger to settle. The browser's own `loadingFailed (canceled)` events
> are the truncation records, flowing through the existing handler
> paths. No timer participates in correctness. Tracked in
> `.claude/todo.kb/2026-07-23-000-*`; two spikes gate it.

The design rule the progression teaches: **never use a duration as a
synchronization primitive.** Every wait must complete on an observable
event; when no event is guaranteed to arrive, *force* one (abort the
request, treat session detach as settlement) rather than sleeping and
hoping. Deadlines are permitted only as watchdogs for "our own machinery
wedged," and firing one is a reportable defect, not a normal path.

## What stays out of scope

Capture records what the client *could have* received over the network
this session. It does not reconstruct data from previous sessions (clear
storage to force a refetch — the fix is upstream of capture), and it
does not guarantee post-cut requests anything.
