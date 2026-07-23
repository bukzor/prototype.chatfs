---
why:
  - capture-implementation-frontier
status: frontier-optimal
owned-loc: "~600"
middleware: "none"
silent-miss: "low"
crash-durable: "good (streamed)"
stealth: "good (real browser, spawned)"
bb1-purity: "pure"
---

# Hand-Rolled CDP Client Over the Debugging Pipe

No browser-automation framework at all: a hand-rolled CDP client
attached to a spawned Chromium over `--remote-debugging-pipe`
(stdio fds, no port, no websocket library) with a managed profile.
Zero third-party product middleware — every failure mode belongs to
this codebase, none of it hidden inside a framework built for page
automation rather than protocol tapping.

Two protocol features remove machinery the current implementation
fights hardest to work around: `Target.setAutoAttach(waitForDebuggerOnStart:
true)` eliminates the popup-attach race by construction (new targets
start paused until resumed), and reading the live browser's UA via
`Browser.getVersion` + overriding it via `Network.setUserAgentOverride`
removes the pre-launch UA cache/probe subsystem entirely.

**What it trades away:** the most owned code of the three
frontier-optimal candidates — everything the frameworks below would
have supplied is now this project's to build and maintain. Best choice
when maximum control and zero framework/vendor exposure matter more
than line count.
