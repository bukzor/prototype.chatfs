---
why:
  - cli-interface
  - validate-pipeline-shape
---

# Three-Subsystem Pipeline

The full pipeline mirrors the BB1→BB2→BB3 decomposition with three subsystems
connected by file I/O:

```
Subsystem A          Subsystem B           Subsystem C
(toy backend)  →     (capture script)  →   (pluck + emit)
serves JSON          produces HAR          extracts + renders
on localhost         via Playwright        to markdown
```

**Subsystem A** is the target — a trivial local web server with known endpoints.
It exists to give Subsystem B something to capture.

**Subsystem B** is the learning target — Playwright browser automation and HAR
recording. This is BB1.

**Subsystem C** is extraction and rendering — HAR parsing, response plucking,
markdown emission. This is BB2+BB3, kept simple since chatgpt-splat already
validates the concepts. **Not implemented in this incubator** — belongs to
downstream pipeline work.

This incubator covers A and B. `toy_pluck.sh` exists as a verification tool
(confirms the HAR contains the expected data) but Subsystem C proper lives
elsewhere.

The subsystems communicate exclusively via files (HAR, extracted.json, markdown).
No shared memory, no IPC. Each is independently runnable and testable.
