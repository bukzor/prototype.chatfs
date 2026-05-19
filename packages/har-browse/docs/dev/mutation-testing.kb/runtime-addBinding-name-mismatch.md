---
status: todo
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

## Hypothesis

`tests/barrier_smoke.spec.mjs` calls
`window.harBrowseMark("BARRIER:end")` page-side. With the registration
name mismatched, `window.harBrowseMark` is undefined and the
`page.evaluate` rejects with a `ReferenceError` (or downstream
`barrierIdx >= 0` assertion fails because no BARRIER ever lands in the
stream). Drive through inject→test→revert to confirm and link the
test.
