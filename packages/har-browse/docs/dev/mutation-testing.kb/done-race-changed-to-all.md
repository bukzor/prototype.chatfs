---
status: done
---

# `capture.mjs`: Promise.race in Done predicate changed to Promise.all

`Promise.race([waitForFunction(...), waitForEvent("close")])` resolves
when *either* signal fires. Change `race` to `all` and termination
requires both — the user has to click "Done" *and* close the window
to end the stream. Otherwise the iterator hangs and the CLI never
exits.

## Injection

`src/capture.mjs`:

```diff
-  const done = Promise.race([
+  const done = Promise.all([
     page.waitForFunction(...),
     context.waitForEvent("close"),
   ])
```

## Test Coverage

`tests/done_predicate.spec.mjs` — "Done-button click alone drains the
events iterator" — clicks `#capture-done` (no context close), then
races the iterator drain against an 8s guard timeout. With `race`
semantics the iterator drains in ~300ms; with `all` semantics the
drain stalls and the guard rejects, failing the test fast.
