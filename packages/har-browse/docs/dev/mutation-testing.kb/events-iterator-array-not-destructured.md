---
status: done
---

# `capture.mjs`: `for await (const [msg] of queue)` destructure dropped

`on(emitter, "event", ...)` yields *arrays* of event-emitter args, not
the args themselves. The `[msg]` destructure pulls out the first arg.
Drop the destructure (`for await (const msg of queue) yield msg`) and
every emitted event becomes a one-element array `[{method, params}]`
on the wire — chrome-har rejects it, downstream consumers see
unexpected shape.

## Injection

`src/capture.mjs`:

```diff
-    for await (const [msg] of queue) yield msg;
+    for await (const msg of queue) yield msg;
```

## Test Coverage

`tests/popup_page.spec.mjs` (and any spec filtering on `m.method`) —
yielded values become single-element arrays, so `m.method`/
`m.params` are `undefined`; every filter/find downstream returns
nothing, failing the assertion. Also caught at type-check time by
`@ts-check` in `capture.mjs:153` — the generator's `AsyncGenerator<
any[], void>` is not assignable to the declared `AsyncIterable<CDPEvent>`.
