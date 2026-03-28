---
why:
  - cli-interface
  - validate-pipeline-shape
---

# Three-Subsystem Pipeline

The full pipeline mirrors the BB1→BB2→BB3 decomposition with three subsystems
connected by file I/O:

```
Subsystem A          Subsystem B
(toy backend)  →     (capture script)
serves JSON          produces HAR
on localhost         via Playwright
```

**Subsystem A** is the target — a trivial local web server with known endpoints.
It exists to give Subsystem B something to capture.

**Subsystem B** is the learning target — Playwright browser automation and HAR
recording. This is BB1.

This incubator covers A and B. `toy_pluck.sh` exists as a verification tool
(confirms the HAR contains the expected data) but full extraction and rendering
(BB2+BB3) lives downstream.

The subsystems communicate exclusively via files (HAR, extracted.json).
No shared memory, no IPC. Each is independently runnable and testable.
