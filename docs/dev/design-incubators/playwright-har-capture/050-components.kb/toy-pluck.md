---
why:
  - three-subsystem-pipeline
  - content-encoding-handling
---

# toy_pluck — HAR → extracted.json

Reads a HAR file, finds the `/api/conversation` response, extracts and
decompresses it, writes `extracted.json`.

## Interface

```
toy_pluck <har-path> --out extracted.json
```

## Responsibilities

- Parse HAR JSON
- Match entries by URL pattern
- Handle content encodings (identity, gzip, brotli, base64)
- Write structured conversation data

## Notes

This is simpler than chatgpt-splat's extraction because the toy conversation
graph is fully controlled. The value is in learning HAR's internal
representation of encoded responses, not in complex parsing.
