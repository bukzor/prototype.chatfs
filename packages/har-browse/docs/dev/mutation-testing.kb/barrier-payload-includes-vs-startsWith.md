---
status: done
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

## Test Coverage

`tests/barrier_smoke.spec.mjs` — "non-anchored 'BARRIER:' substring
isn't deferred". Awaits N=10 parallel /payload fetches so every
loadingFinished has arrived and N body-fetches sit in `inFlight`,
then immediately issues `window.harBrowseMark("debug-BARRIER:foo")`.
Under `startsWith` the binding emits at its natural CDP position
(before the RRs whose body-fetches haven't resolved). Under `includes`
the binding is deferred behind the in-flight drain and lands after
the last /payload RR — assertion `bindingIdx < lastPayloadRRIdx`
fails.
