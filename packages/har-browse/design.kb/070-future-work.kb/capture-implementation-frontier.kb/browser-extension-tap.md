---
why:
  - capture-implementation-frontier
status: frontier-optimal
owned-loc: "~450"
middleware: "browser extension platform (MV3)"
silent-miss: "low"
crash-durable: "good (streamed to a local sink)"
stealth: "perfect (user's own daily browser)"
bb1-purity: "pure"
---

# Extension Using `chrome.debugger` in the User's Daily Browser

An MV3 extension attaches CDP via `chrome.debugger` inside the browser
the human already uses every day — same tap point as the spawned-browser
candidates, different host. Nothing to launch, no profile to manage:
the user is already logged into every site that matters, in their
native fingerprint. A toolbar button replaces the injected-overlay Done
control. Streams captured events to a small localhost sink for
`crash-durability`.

**What it trades away:** MV3 service-worker lifecycle quirks, the
"this page is being debugged" banner Chrome shows while attached,
Chrome-only, and exposure to extension-store review/policy churn. Best
choice when login UX and native fingerprint dominate every other
concern.
