---
why:
  - toy-pluck
  - content-encoding-handling
---

# M3 — Extraction

Plucker reliably extracts the `/api/conversation` response from the
JSONL event stream.

## Acceptance

- `toy_pluck.sh < events.jsonl > extracted.json` produces the correct
  conversation graph
- Handles base64-wrapped bodies (Chromium base64-encodes non-text MIME
  types; HTTP-level compression is already decompressed by Chromium)
- Handles multiple matching events (emits all matches)
