---
why:
  - capture-implementation-frontier
status: dominated
owned-loc: "~250"
middleware: "MITM proxy (e.g. mitmproxy)"
silent-miss: "medium (cache-served responses invisible)"
crash-durable: "good (streamed)"
stealth: "poor (proxy's TLS fingerprint, not the browser's)"
bb1-purity: "pure"
---

# MITM Proxy (e.g. mitmproxy Addon)

Sit in the byte path instead of tapping a protocol: bodies arrive
inline, so the entire in-flight body-fetch/drain/barrier apparatus
dissolves structurally rather than shrinking incrementally. Least
owned code of any candidate considered, including the two
frontier-optimal designs with less code than this one's category
average.

**Why it's dominated, not frontier:** vetoed twice over, both against
requirements no amount of extra code buys back. The proxy's TLS
fingerprint is its own, not the browser's — directly adversarial to
`unblocked-sessions` on exactly the bot-gated sites this tool targets.
And cache-served responses never cross the wire at all — a silent hole
in `capture-everything` that stays invisible until someone notices a
response the browser plainly had.

Illustrative because "least code" and "best design" diverge sharply
here: the axis that kills it (fingerprint + cache-invisibility) isn't
about code volume at all.
