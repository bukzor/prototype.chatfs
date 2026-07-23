---
why:
  - capture-implementation-frontier
status: frontier-optimal
owned-loc: "~300"
middleware: "puppeteer-core (Node)"
silent-miss: "low"
crash-durable: "good (streamed)"
stealth: "good (real browser, spawned)"
bb1-purity: "pure"
---

# `puppeteer-core` on a Spawned Browser

A small CDP-capable automation library (no bundled Chromium download,
no page-automation surface beyond what's needed to attach and drive
network capture) fills the role `pure-cdp-spawned.md` hand-rolls:
target/session management, protocol framing, event dispatch. Owned
code is the launcher, profile handling, drain/termination logic, and
JSONL emission — meaningfully less than writing a CDP client from
scratch.

**Where it sits on the frontier:** non-dominated against the other
three. It beats `pure-cdp-spawned.md` on owned lines (~300 vs. ~600) at
the cost of one small dependency; it beats `recordhar-thin-wrapper.md`
on `crash-durability` (events stream as they arrive; nothing is
batched at close) at the cost of more owned lines (~300 vs. ~150); it
beats `browser-extension-tap.md` on owned lines at the cost of
stealth (a spawned browser, not the user's own). No existing candidate
matches it on every axis at once — a genuine fourth point on the
frontier, not a compromise that loses to one of the others outright.
