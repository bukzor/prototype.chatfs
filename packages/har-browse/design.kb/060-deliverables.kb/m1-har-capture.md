---
why:
  - toy-capture
  - capture-cut-completeness
---

# M1 — HAR-Derivable Capture

har-browse captures a single page load as a JSONL CDP event stream from
which a valid HAR is derivable downstream.

## Acceptance

- `har-browse` emits one CDP event per line in the `{method, params}`
  shape `chrome-har` consumes, response bodies attached
- The stream covers `/`, `/index.css`, `/index.js`, `/api/conversation`
- `chrome-har`'s `harFromMessages` derives a valid HAR from the stream
  (`src/cdp_to_har.mjs`; exercised by `tests/har.spec.mjs`)
- Script exits 0 on success
