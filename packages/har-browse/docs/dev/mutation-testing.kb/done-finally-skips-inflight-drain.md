---
status: done
---

# `capture.mjs`: finally doesn't drain in-flight before `end`

`done`'s `.finally` awaits `Promise.allSettled([...inFlight])` before
`emitter.emit("end")`, holding the events iterator open until every
tracked promise settles. Drop the drain and any tracker whose enqueue
hasn't fired yet races against the queue close — capture emits
queue-close while the tracker still has work pending, and downstream
HAR is missing whatever that tracker would have enqueued.

`inFlight` carries three categories of trackers:
1. `wireSession(p)` promises (per-page CDP attach + handler install)
2. `onLoadingFinished(p)` promises (body-fetch + RR/LF enqueue)
3. Deferred BARRIER promises (`allSettled` snapshot + bindingCalled enqueue)

## Injection

`src/capture.mjs`:

```diff
     .finally(async () => {
-      await Promise.allSettled([...inFlight]);
       emitter.emit("end");
     })
```

## Test Coverage

`tests/popup_race.spec.mjs:19` — "popup wireSession is awaited at close
(slow CDP attach)". Monkey-patches `context.newCDPSession` to delay
`Runtime.enable` by 500ms in popup sessions; the popup's `wireSession`
promise stays in `inFlight` long after the popup's /payload events
have been delivered into our session. Clicking Done before the
wireSession completes leaves a tracker in `inFlight`. With the drain,
`.finally` awaits the slow wireSession before `emit("end")`, and the
popup's RR makes the queue. Without the drain, `emit("end")` fires
immediately, the popup's RR enqueue happens after — dropped.

## See Also

Prior attempts to reproduce the LF-handler in-flight regime via large
response bodies (`?size=N` toy-server padding) or fire-and-forget
fetch loops failed: by the time `page.waitForFunction(...)` polling
detects `dataset.clicked` (~RAF) and `.finally` runs, the LF
handlers' CDP body-fetches have already completed. The
wireSession-delay regime in `popup_race.spec.mjs` is the only test
where the drain demonstrably matters — but that one mutation kill
suffices to gate the drain.
