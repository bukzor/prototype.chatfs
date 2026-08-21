---
why:
  - ../capture-implementation-frontier.md
status: dominated
owned-loc: "~250"
middleware:
  "@value": "MITM proxy"
  description: "e.g. mitmproxy"
silent-miss:
  "@value": "medium"
  description: "cache-served responses invisible"
crash-durable:
  "@value": "good"
  description: "streamed"
stealth:
  "@value": "poor"
  description: "proxy's TLS fingerprint, not the browser's"
bb1-purity: "pure"
---

# MITM Proxy (e.g. mitmproxy Addon)

Sit in the byte path instead of tapping a protocol: bodies arrive
inline, so the entire in-flight body-fetch/drain/barrier apparatus
dissolves structurally rather than shrinking incrementally.

**Why it's dominated, not frontier:** vetoed twice over, both against
requirements no amount of extra code buys back. The proxy's TLS
fingerprint is its own, not the browser's — directly adversarial to
`unblocked-sessions` on exactly the bot-gated sites this tool targets.
And cache-served responses never cross the wire at all — a silent hole
in `capture-everything` that stays invisible until someone notices a
response the browser plainly had.

Illustrative because the win and the vetoes share one root: sitting in
the byte path is what delivers bodies inline — and equally what swaps
in the proxy's TLS fingerprint and hides cache-served responses. The
placement that makes the design cheap is the placement that loses.
