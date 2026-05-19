---
status: done
---

# `capture.mjs`: BARRIER prefix check case-mismatches the page contract

Page-side code calls `harBrowseMark("BARRIER:...")`. The capture-side
check is `params.payload?.startsWith?.("BARRIER:")`. Mutating to
`"Barrier:"` (or any other casing) decouples capture from page;
every BARRIER marker falls through to the no-defer branch and emits
immediately — same downstream effect as
`barrier-emit-before-bodies-settle` but with a different proximate
cause.

## Injection

`src/capture.mjs`, in `onBindingCalled`:

```diff
-        params.payload?.startsWith?.("BARRIER:")
+        params.payload?.startsWith?.("Barrier:")
```

## Test Coverage

`tests/barrier_smoke.spec.mjs`: same precede-BARRIER-in-stream
assertion catches this — the case-mismatched prefix means *every*
`BARRIER:`-payload marker falls through to the no-defer branch and
emits immediately, before body-fetches settle.
