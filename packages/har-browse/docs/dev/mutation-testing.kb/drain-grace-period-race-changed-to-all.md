---
status: todo
---

# `capture.mjs`: bounded-drain `Promise.race` swapped to `Promise.all`

**Priority:** High. **Confidence:** Medium.

Prospective — targets the fix in `packages/har-browse/.claude/todo.kb/
2026-07-22-000-Done-Capturing-race-drops-in-flight-requests-with-no-
drain.md`, not yet implemented.

Initially expected this to be a mild, opposite-direction latency bug
("always waits the full grace period even when everything finishes
instantly"). On inspection it is not: `Promise.all([A, B])` only
resolves once *every* argument resolves. If `A` (`Promise.allSettled(
[...inFlight])`) never resolves — because some tracked request never
reaches a terminal event — then `Promise.all` never resolves either,
regardless of `B`'s timeout firing after `DRAIN_GRACE_MS`. This
mutation therefore reintroduces **the identical indefinite-hang defect**
as `drain-grace-period-removed.md`, not a distinct milder one. Filed
separately because it's a distinct, plausible fat-finger mutation
(`race`↔`all` is a standard mutation-testing operator) that a mutation
tool would generate independently of the "delete the timeout entirely"
mutation, even though the two collapse to the same observable bug.

## Injection

```diff
-    await Promise.race([
+    await Promise.all([
       Promise.allSettled([...inFlight]),
       new Promise((resolve) => setTimeout(resolve, DRAIN_GRACE_MS)),
     ]);
```

## Anticipated Test Coverage

Same hang-fixture test as `drain-grace-period-removed.md` should kill
this mutant too — worth confirming both are caught by one test rather
than writing near-duplicate coverage. Medium confidence for the same
reason as that entry.
