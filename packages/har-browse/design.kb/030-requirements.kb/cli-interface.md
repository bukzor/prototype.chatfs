---
why:
  - validate-pipeline-shape
---

# CLI Interface

Each pipeline stage is a standalone CLI tool:

- `har-browse [URL] [--har PATH] [--profile NAME] [--howto PATH]`
- `toy_pluck.sh < har > extracted.json`

Defaults: URL `http://127.0.0.1:8000`, `--har out.har`, `--profile default_profile`.

Exit codes:

- `0` — success (user clicked "Done Capturing"; HAR finalized)
- `2` — user cancelled (closed the window); halts the pipeline
- `1` — reserved for genuine errors (Playwright throw, unwritable HAR path, etc.)

Diagnostic output goes to stderr.

**Verification:** The full pipeline runs as a shell one-liner:
`har-browse && toy_pluck.sh < out.har > extracted.json`
(A cancelled capture exits 2, short-circuiting `&&`.)
