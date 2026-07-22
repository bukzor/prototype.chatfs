---
status: todo
---

# `capture.mjs`: redirect re-entrancy guard dropped from `requestWillBeSent` tracking

**Priority:** Medium-Low. **Confidence:** Low-Medium.

Prospective — targets the fix in `packages/har-browse/.claude/todo.kb/
2026-07-22-000-Done-Capturing-race-drops-in-flight-requests-with-no-
drain.md`, not yet implemented.

CDP re-fires `Network.requestWillBeSent` with the *same* `requestId` for
each redirect hop. The planned handler guards against this
(`if (!pendingRequests.has(p.requestId))`) so a single logical request
gets exactly one tracked promise, resolved once at the eventual terminal
event. If the guard is dropped, each hop overwrites the map entry with a
fresh resolver, silently orphaning the previous hop's promise (already
in `inFlight`, never resolved) — a shutdown-latency regression (forces
the grace-period timeout), not data loss.

## Injection

```diff
   "Network.requestWillBeSent": (p) => {
-    if (!pendingRequests.has(p.requestId)) {
-      let resolve;
-      const pr = new Promise((res) => { resolve = res; });
-      pendingRequests.set(p.requestId, resolve);
-      track(pr);
-    }
+    let resolve;
+    const pr = new Promise((res) => { resolve = res; });
+    pendingRequests.set(p.requestId, resolve);
+    track(pr);
     enqueue({ method: "Network.requestWillBeSent", params: p });
   },
```

## Anticipated Test Coverage

Needs a fixture that issues at least one redirect (e.g. a toy-server
route returning `302` before the final response) combined with the same
timing assertion as the `pending-request-not-resolved-on-*` entries.
Confidence is Low-Medium rather than Medium: no existing toy-server route
does a redirect today (unlike the delayed-response regime `popup_race
.spec.mjs` already established a pattern for), so this needs new fixture
infrastructure before it's even testable — may be more efficient to fold
into whichever test covers the `not-resolved` mutations, using a
redirect-then-delay fixture that exercises both at once.
