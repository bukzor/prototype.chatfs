---
status: gap
attempts: 1
---

# `capture.mjs`: `awaitingBody` map shared across CDP sessions

Currently declared inside `wireSession` — each per-page CDP session
owns its own `awaitingBody`. Hoist it to `attachCapture` scope and the
map becomes shared across sessions. The fear: CDP requestIds aren't
globally unique, so cross-session collisions cause LF from page A to
look up an RR stashed by page B, attaching the wrong body and silently
corrupting the capture.

## Injection

`src/capture.mjs`:

```diff
   const emitter = new EventEmitter();
   const queue = on(emitter, "event", { close: ["end"] });
+  /** @type {Map<string, any>} */
+  const awaitingBody = new Map();

   /** @param {Page} subject */
   const wireSession = async (subject) => {
     const session = await context.newCDPSession(subject);
-    /** @type {Map<string, any>} */
-    const awaitingBody = new Map();
```

## Test Result

Full e2e suite (17 tests) passes with the mutation injected. The
predicted cross-session collision does not occur in practice.

### Why

Empirically probed CDP requestId format: `<targetId>.<counter>` where
`targetId` is a process-global integer Chromium assigns at devtools-
target creation, plus a per-navigation UUID-prefixed id for the first
RR. Targets get unique ids even across separate browser processes
(different persistent-context launches): two `launchPersistentContext`
runs in the same Node process produced prefixes `20996` and `21056`,
never overlapping. Within one browser, two pages of the same context
got prefixes `20305` and `20338`.

The `.<counter>` part is per-target. Since the target prefix differs
between any two CDP sessions, the (prefix, counter) tuple — which is
what the requestId string is — never collides between sessions.

### Forcing a collision

The bug *can* be triggered only by manufacturing a collision via one
of:

1. Faking the CDP transport in a unit test and injecting RR/LF pairs
   with chosen ids. Doable but requires re-creating the entire
   `wireSession` plumbing in mocks — testing the test more than the
   code.
2. A future Chromium protocol change that reuses ids across targets
   (no evidence this is planned).
3. A future feature that synthesizes events with custom requestIds.

None apply to the current code. Per-session scoping defends against
condition (2)/(3) becoming true — useful intent, not currently
observable behavior.

## See Also

`awaiting-body-not-deleted` — same map, also unobservable (different
reason: Map.set overwrites on collision, no behavioral difference at
the LF side either).
