---
why:
  - validate-pipeline-shape
---

# CLI Interface

Each pipeline stage is a standalone CLI tool:

- `toy_capture --url <url> --har <path> [--headful]`
- `toy_pluck <har-path> --out <json-path>`
- `toy_emit <json-path> --outdir <dir>`

Each tool exits 0 on success, nonzero on failure, and writes diagnostic output
to stderr.

**Verification:** The full pipeline runs as a shell one-liner:
`toy_capture ... && toy_pluck ... && toy_emit ...`
