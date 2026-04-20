---
why:
  - validate-pipeline-shape
---

# CLI Interface

Each pipeline stage is a standalone CLI tool:

- `toy_capture/capture.mjs [URL] [--har PATH] [--howto PATH]`
- `toy_pluck.sh < har > extracted.json`

Each tool exits 0 on success, nonzero on failure, and writes diagnostic output
to stderr.

**Verification:** The full pipeline runs as a shell one-liner:
`./toy_capture/capture.mjs && ./toy_pluck.sh < out.har > extracted.json`
