---
status: todo
---

# `capture.mjs`: BARRIER prefix check uses `includes` instead of `startsWith`

`startsWith("BARRIER:")` is anchored — only payloads beginning with the
prefix defer. Switching to `includes("BARRIER:")` allows any payload
that *contains* the substring to be deferred. Future binding payloads
that legitimately mention "BARRIER:" (e.g. a debug-log marker, a
serialized event with the word in it) get spuriously deferred — wrong
ordering semantics for those events.

## Injection

`src/capture.mjs`, in `onBindingCalled`:

```diff
-        params.payload?.startsWith?.("BARRIER:")
+        params.payload?.includes?.("BARRIER:")
```

## Fixture needed

Add a non-BARRIER `harBrowseMark` call from the page with payload
containing `"BARRIER:"` mid-string (e.g.
`"debug-saw-BARRIER:foo-elsewhere"`). Assert the binding event emits
immediately (not deferred). Without anchoring, the test sees the
binding emit after in-flight bodies settle — order violation flagged by
a precede-binding-in-stream check or an immediate-emit timestamp delta.
