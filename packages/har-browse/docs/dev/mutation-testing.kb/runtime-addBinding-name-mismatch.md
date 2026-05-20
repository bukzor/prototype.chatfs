---
status: done
---

# `capture.mjs`: `Runtime.addBinding` name doesn't match page-side caller

`Runtime.addBinding({ name: "harBrowseMark" })` makes
`window.harBrowseMark` exist on the page. Test/page code calls
`window.harBrowseMark("BARRIER:...")`. Mismatch the registration name
and the page-side call throws `ReferenceError` — BARRIERs never fire,
the entire ordering invariant collapses (no `Runtime.bindingCalled`
events at all).

Distinct from `barrier-binding-name-wrong`, which is on the *filter*
side (`params.name === "harBrowseMark"`): the binding fires there but
the deferral arm doesn't match. This mutation is upstream — bindings
don't fire at all.

## Injection

`src/capture.mjs`, in `wireSession`:

```diff
-    await session.send("Runtime.addBinding", { name: "harBrowseMark" });
+    await session.send("Runtime.addBinding", { name: "HarBrowseMark" });
```

## Test Coverage

`tests/barrier_smoke.spec.mjs` — with the registration name
mismatched, the page-side `window.harBrowseMark("BARRIER:end")` throws
`TypeError: window.harBrowseMark is not a function`; the
`page.evaluate` rejects before the click and the test fails fast
(~600ms).
