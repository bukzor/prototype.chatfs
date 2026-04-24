---
why:
  - cli-interface
  - validate-pipeline-shape
---

# Three-Subsystem Pipeline

The full pipeline mirrors the BB1→BB2→BB3 decomposition with three subsystems
connected by Unix pipes/files:

```
Subsystem A          Subsystem B
(toy backend)  →     (capture script)
serves JSON          streams CDP events (JSONL)
on localhost         via Playwright
```

**Subsystem A** is the target — a trivial local web server with known endpoints.
It exists to give Subsystem B something to capture.

**Subsystem B** is the learning target — Playwright browser automation plus
a CDP event passthrough. This is BB1. Output is JSONL in chrome-har's wire
shape (`{method, params}`), which downstream tools can consume directly
(e.g. `chrome-har`'s `harFromMessages` produces a bonafide HAR document on
demand — no HAR-reconstruction logic lives in this repo).

This incubator covers A and B. `toy_pluck.sh` exists as a verification tool
(confirms the event stream carries the expected response body) but full
extraction and rendering (BB2+BB3) lives downstream.

The subsystems communicate via Unix pipes (stdout → stdin) or intermediate
files. No shared memory, no IPC. Each is independently runnable and testable.
