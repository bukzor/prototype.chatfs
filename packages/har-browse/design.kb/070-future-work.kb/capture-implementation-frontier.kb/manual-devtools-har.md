---
why:
  - capture-implementation-frontier
status: dominated
owned-loc: "~0"
middleware: "none"
silent-miss: "low (human error: forgotten preserve-log, missed click)"
crash-durable: "poor (single manual export, no incremental record)"
stealth: "perfect (user's own browser)"
bb1-purity: "pure"
---

# Manual DevTools "Save as HAR (with Content)"

The human opens their own browser's DevTools, ticks "preserve log,"
and clicks "Save as HAR with content" by hand. Zero owned code, full
response bodies, the user's own browser and existing logins.

**Why it's dominated, not frontier:** this is the baseline every other
candidate's owned code has to out-perform, not a workable design on
its own. It fails on toil (a manual step repeated every session, with
nothing automated to fall back on) and on `crash-durability` (a
forgotten "preserve log" checkbox, a missed click, or a crash mid-session
loses the capture with no record that it happened).

Kept as the reference point: any candidate that can't clearly beat this
one on some axis isn't earning its owned code.
