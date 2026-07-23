---
why:
  - capture-implementation-frontier
status: dominated
owned-loc: "~250"
middleware: "none"
silent-miss: "high (workers, WebSockets, SSE, anything unwrapped)"
crash-durable: "good (streamed)"
stealth: "perfect (no separate browser instance)"
bb1-purity: "pure-ish (in-page hooks brush against page internals)"
---

# In-Page `fetch`/XHR Wrapping

Monkey-patch `fetch` and `XMLHttpRequest` in injected page JS. No
browser-automation layer at all beyond driving navigation — on paper
the cheapest candidate in the set.

**Why it's dominated, not frontier:** vetoed by silent-miss risk, the
decisive axis. It misses document loads and any subresource not
fetched through the wrapped APIs, plus workers, WebSockets, and SSE
entirely — and there is no way to detect what was missed, because the
miss happens outside any code this design controls. `capture-everything`
is precisely the guarantee this design cannot make, and cannot even
report failing to make.

Illustrative as the shape "small code, unbounded blind spot" takes —
the failure mode `capture-everything` exists to rule out.
