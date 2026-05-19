---
status: done
---

# `capture.mjs`: BARRIER check uses wrong binding name

`Runtime.addBinding({ name: "harBrowseMark" })` registers the page-side
function `window.harBrowseMark`. The capture-side filter is
`params.name === "harBrowseMark"`. A typo here means *every* binding
event falls through the BARRIER-check arm — but more importantly, no
BARRIER ever defers and ordering breaks for every `BARRIER:` mark.

## Injection

`src/capture.mjs`, in `onBindingCalled`:

```diff
-        params.name === "harBrowseMark" &&
+        params.name === "HarBrowseMark" &&
```

## Test Coverage

`tests/barrier_smoke.spec.mjs`: same precede-BARRIER-in-stream
assertion catches this. Wrong binding name means the BARRIER check
never matches; markers fall through to immediate-emit and at least one
in-flight body-fetch RR lands after the marker.
