---
why:
  - three-subsystem-pipeline
  - content-encoding-handling
---

# toy_pluck — HAR → extracted.json

Reads a Playwright HAR from stdin, finds the `/api/conversation` response,
decodes it, writes the conversation JSON to stdout.

## Interface

```
toy_pluck.sh < out.har > extracted.json
```

## Responsibilities

- Parse HAR JSON
- Match entries by URL pattern
- Handle HAR-level base64 encoding (Playwright decodes HTTP-level compression
  like gzip/brotli before writing the HAR; the only encoding toy_pluck handles
  is the HAR's own base64 wrapper)
- Write structured conversation data

## Notes

This is simpler than chatgpt-splat's extraction because the toy conversation
graph is fully controlled. Implemented as a single jq filter.
