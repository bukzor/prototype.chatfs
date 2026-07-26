# Sec-CH-UA brand list

**Verdict: not implemented. Strongest candidate for adding.**

A site that reads only client hints — an increasing share — sees no
disclosure from us today. The `User-Agent` channels reach the rest; this
one reaches those.

The brand list is designed for exactly this: unordered and extensible,
and Chromium already ships a GREASE entry (`"Not)A;Brand"`), so sites
must already tolerate brands they do not recognize.

```json
"brands": [
  {"brand": "Chromium", "version": "147"},
  {"brand": "Google Chrome", "version": "147"},
  {"brand": "har-browse", "version": "1"}
]
```

## Two things to get right

The token must go into **both** `brands` and `fullVersionList`. If the
two lists disagree, that inconsistency is itself detectable — more so
than the disclosure it was meant to carry.

It is unmeasured against the aistudio gate. `Sec-CH-UA` may get the same
shape check the `User-Agent` string does, which is the sort of thing to
learn before shipping rather than after. Testing it needs
`../ua-position-gate.mjs` fixed to send `userAgentMetadata` first — see
the method caveat in `../ua-position-gate.md`.

## Cost to implement

Small. `userAgentMetadata()` already reads the browser's true metadata
and `hostSession()` already sends it, so this is an insertion into an
existing structure rather than new machinery.
