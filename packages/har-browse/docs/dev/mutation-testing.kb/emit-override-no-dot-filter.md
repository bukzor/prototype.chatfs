---
status: todo
---

# `capture.mjs`: emit-override drops the `"."` filter on event names

`sessionBus.emit` is overridden to intercept CDP-style event names
(`Network.responseReceived`, etc.) — gated on `typeof name === "string"
&& name.includes(".")` so internal EventEmitter events (`close`,
`error`, plus Playwright's own non-CDP events) pass through without
being mistaken for CDP. Drop the `.` filter and every internal emit
gets shoved into the queue as `{ method: "close", params: {} }` (or
similar) — chrome-har sees nonsense events and may error or produce
junk entries.

## Injection

`src/capture.mjs`, in the emit-override:

```diff
-      if (typeof name === "string" && name.includes(".")) {
+      if (typeof name === "string") {
```

## Fixture needed

Assert the captured event stream contains no `method`s without a `.`
separator (i.e., every method matches `/\w+\.\w+/`). Could add to any
existing capture-driven spec.
