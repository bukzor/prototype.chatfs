---
status: todo
---

# `capture.mjs`: `DRAIN_GRACE_MS` zeroed (timeout always wins the race)

**Priority:** High. **Confidence:** High.

Prospective — targets the fix in `packages/har-browse/.claude/todo.kb/
2026-07-22-000-Done-Capturing-race-drops-in-flight-requests-with-no-
drain.md`, not yet implemented. Opposite-direction twin of
`drain-grace-period-removed.md`: instead of the timeout vanishing (hang),
the timeout fires immediately (constant zeroed, or a units fat-finger
like `2000` → `2`). The bounded drain then waits for nothing, and a
request that's in flight at "Done Capturing" — the exact case fix 1
exists for — is dropped again. The whole tracking mechanism survives in
code but is dead weight: this is the stealthiest way for the original
bug to regress, because every structural piece of the fix remains
present.

## Injection

```diff
-const DRAIN_GRACE_MS = 2000;
+const DRAIN_GRACE_MS = 0;
```

## Anticipated Test Coverage

The same assertion that gates `pending-request-not-tracked.md`: a
fixture response that completes after the Done click but within the
grace period must appear in the drained stream, body and all. That test
inherently requires the grace period to be genuinely honored, so it
kills this mutant with no additional construction. Note the corollary:
that test must pin (or inject) a known `DRAIN_GRACE_MS` — if the
constant is configurable via `startCapture`, the test should set it
explicitly rather than rely on the default, or this mutation escapes.
