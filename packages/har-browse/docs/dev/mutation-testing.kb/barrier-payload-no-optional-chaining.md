---
status: todo
---

# `capture.mjs`: `params.payload?.startsWith?.` optional chains dropped

Non-BARRIER bindings (any future page-side `window.harBrowseMark(...)`
caller that passes a non-string or undefined payload) reach
`onBindingCalled` with `params.payload` undefined. The `?.startsWith?.`
chain returns undefined safely; without it, the call throws and the
CDP emit-override propagates the throw, crashing the capture stream.

## Injection

`src/capture.mjs`, in `onBindingCalled`:

```diff
       if (
         params.name === "harBrowseMark" &&
-        params.payload?.startsWith?.("BARRIER:")
+        params.payload.startsWith("BARRIER:")
       ) {
```

## Fixture needed

Page-side call `window.harBrowseMark()` (no payload). Assert the
capture stream still produces events for subsequent network activity
(i.e., capture didn't die). Without the optional chaining, the
TypeError propagates out of the emit-override and kills downstream
flow.
