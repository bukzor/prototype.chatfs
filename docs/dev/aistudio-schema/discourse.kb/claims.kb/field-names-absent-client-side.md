---
status: asserted
likelihood: 0.9
sources: [sources.kb/live-replay-probe.md, sources.kb/bundle-audit.md]
tags: [aistudio, schema, coverage, doubt]
---

The conversation's receive-path field names exist **only in the server's
`?alt=json` projection**, never client-side. Searching the bundles and both CDP
captures (case-insensitive, incl. snake_case / kebab-case) finds no
`chunkedPrompt` / `isThought` / `thoughtSignature` in any form — only the
unrelated enum value `CHUNKED_PROMPT` in `metadata.customProperties`. Only
*send/config*-path names (`runSettings`, `maxOutputTokens`, `topP`, `topK`)
appear as bundle string literals.

The CDP holds no hidden copy either: no websocket/SSE frames, no `base64Encoded`
bodies, no stored compression — `dataReceived` events carry only byte counts,
and response bodies are plaintext. So **offline, RE-free decoding of the turn
structure is not possible from the current artifacts**: the names simply are not
present to extract.

Uncertainty (<1.0): the absence is established for the specific tokens probed
and the encodings ruled out; 22 captured responses have no stored body and were
not enumerated, a small residual gap.
