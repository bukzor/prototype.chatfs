---
why:
  - reusable-capture-components
---

# M5 — Adversarial Cases

Stress the pipeline with edge cases that will occur in real capture scenarios.

## Cases

- Multiple conversation fetches in a single HAR
- Delayed responses (server-side latency)
- Mixed content encodings within one HAR
- Large payloads (compression ratio, streaming)
- Interrupted captures (browser crash, network timeout)

## Acceptance

- Pipeline handles each case without silent corruption
- Failures produce clear error messages on stderr
- No case produces truncated or partial output without a nonzero exit code
