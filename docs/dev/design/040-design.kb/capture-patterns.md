---
why:
  - opaque-extractor-boundary
  - black-box-decomposition
source:
  - conversations.cleaned/02-architecture-convergence/094.assistant.text.md
---

# Five Capture Patterns (BB1 Implementation Options)

Five viable patterns for the browser-side capture component emerged during
design. All use Playwright/Puppeteer. Listed from cleanest UX to most
policy-safe:

**Pattern 1 — Inject UI button, read from page state**
`addInitScript` injects a floating "Export" button. On click, injected JS pulls
conversation from app state, serializes it, triggers a download or copies to
clipboard. Alternatively, use `exposeFunction` to hand the payload directly to
the daemon (recommended handoff — avoids downloads folder and clipboard).

**Pattern 2 — Inject UI button, export from DOM**
Button walks rendered DOM, builds best-effort transcript. More stable to
internal state changes but loses fork metadata.

**Pattern 3 — Network event sniffer**
Playwright subscribes to network events, captures response bodies when the
"right" response happens after a refresh. Robust technically, but explicitly
"network sniffer" territory.

**Pattern 4 — Raw CDP capture**
`CDPSession` for DevTools-level traffic capture. Similar to Pattern 3 but more
DevTools-native.

**Pattern 5 — Assisted manual with wizard**
Inject UI that guides clicks, detects refresh, tells user "now save HAR." Least
magic, most policy-safe, still a huge ergonomic win over raw DevTools.

All patterns fall inside the opaque extractor boundary — the user implements
these, assistants do not help with service-specific targeting.
