---
why:
  - capture-implementation-frontier
status: frontier-optimal
owned-loc: "~150"
middleware: "automation framework w/ built-in recorder (e.g. Playwright)"
silent-miss: "low"
crash-durable: "poor (written at context close)"
stealth: "good (real browser, spawned)"
bb1-purity: "pure"
---

# Thin Wrapper Around the Browser's Own HAR Recorder

Launch a browser with its built-in HAR-recording facility enabled
(e.g. Chromium's `recordHar` context option) and own only the launcher,
profile handling, and the in-flow termination signal. The recorder
itself does body capture, encoding, and HAR assembly — no drain, no
barrier, no body-fetch machinery to write.

Fewest owned lines among the reliable candidates: this is what "use the
tool with the grain" looks like once the CDP-shaped JSONL record is no
longer a fixed requirement.

**What it trades away:** the recorder writes its HAR at context close,
batched. A crash mid-session — browser, process, or machine — loses the
entire capture, not just the tail. `crash-durability` fails outright;
the only mitigation is operator habit (shorter sessions), not code.
Best choice when session length stays modest and owned-code minimalism
dominates.
