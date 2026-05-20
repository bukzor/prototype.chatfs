---
status: gap
attempts: 1
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

## Test Result

The defended-against case is not reachable in practice. Playwright /
CDP `Runtime.addBinding` only accepts string payloads — calling
`window.harBrowseMark()` page-side throws
`Error: Invalid arguments: should be exactly one string` at the
binding layer, before `Runtime.bindingCalled` is dispatched. Same for
non-string args. The optional chains defend against an undefined
`params.payload`, which CDP guarantees is a string. No page-side
invocation can reach the `.startsWith` call on undefined.

Tried: `page.evaluate(() => window.harBrowseMark())` — Playwright
rejects before the binding fires. Other non-string payloads behave
the same.

This mutation is unreachable; the `?.` chains are dead defense. Could
be safely removed from the implementation, but leaving them in keeps
the code robust against any future protocol change.
