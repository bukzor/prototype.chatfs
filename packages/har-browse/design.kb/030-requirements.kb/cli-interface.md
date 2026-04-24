---
why:
  - validate-pipeline-shape
---

# CLI Interface

Each pipeline stage is a standalone CLI tool:

- `har-browse [URL] [--profile NAME] [--howto PATH] > events.jsonl`
- `toy_pluck.sh < events.jsonl > extracted.json`

Defaults: URL `http://127.0.0.1:8000`, `--profile default_profile`.

`har-browse` writes its CDP event stream to stdout; redirect or pipe to
consume it. There is no `--har` flag — HAR documents are produced
downstream (e.g. via `chrome-har`'s `harFromMessages`) on demand.

Exit codes:

- `0` — success (user clicked "Done Capturing"; stream flushed)
- `2` — user cancelled (closed the window); halts the pipeline
- `1` — reserved for genuine errors (Playwright throw, etc.)

Diagnostic output goes to stderr.

**Verification:** The full pipeline runs as a shell one-liner:
`har-browse | toy_pluck.sh > extracted.json`.
