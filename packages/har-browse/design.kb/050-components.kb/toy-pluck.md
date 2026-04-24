---
why:
  - three-subsystem-pipeline
  - content-encoding-handling
---

# toy_pluck — CDP events → extracted.json

Reads a JSONL CDP event stream from stdin, finds the
`Network.responseReceived` event whose response URL matches
`/api/conversation`, decodes the body, writes the conversation JSON to
stdout.

## Interface

```
toy_pluck.sh < events.jsonl > extracted.json
```

## Responsibilities

- Parse JSONL (one event per line)
- Match on `method == "Network.responseReceived"` and
  `params.response.url` pattern
- Handle base64-encoded bodies (Chromium returns `base64Encoded: true`
  from `Network.getResponseBody` for non-text MIME types)
- Write structured conversation data

## Notes

This is simpler than chatgpt-splat's extraction because the toy conversation
graph is fully controlled. Implemented as a single jq filter.
