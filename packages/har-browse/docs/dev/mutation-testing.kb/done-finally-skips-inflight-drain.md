---
status: gap
attempts: 1
---

# `capture.mjs`: finally doesn't drain in-flight before `end`

After Done click, bodies for already-finished requests may still be
fetching via `Network.getResponseBody`. The finally `await
Promise.allSettled([...inFlight])` is the only thing that holds the
queue open until those land. Drop it and any post-click body emits
race against the `"end"` event — capture emits a queue-close before
the bodies arrive, and downstream HAR is missing them.

## Injection

`src/capture.mjs`:

```diff
     .finally(async () => {
-      await Promise.allSettled([...inFlight]);
       emitter.emit("end");
     })
```

## Test Result

All 8 Playwright tests pass with the drain dropped. Same root cause as
`barrier-promise-not-tracked`: existing tests await
`Promise.all(fetches)` page-side before clicking Done, so by the time
Done fires there are no in-flight body fetches left to drain. To
catch this, a test would need to issue requests whose response bodies
land *after* the Done click — concretely, a long-delayed
`/payload?delay=300` started just before clicking. The captured
events for that delayed request would then be missing post-mutation.
Defer to a follow-up test fixture; behavior is real, just not
exercised.
