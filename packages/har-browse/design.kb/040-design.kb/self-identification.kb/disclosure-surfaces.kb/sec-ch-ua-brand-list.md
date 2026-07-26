# Sec-CH-UA brand list

**Verdict: not implemented. Measured viable — the candidate to add.**

A site that reads only client hints — an increasing share — sees no
disclosure from us today. The `User-Agent` channels reach the rest; this
one reaches those.

The brand list is designed for exactly this: unordered and extensible,
and Chromium already ships a GREASE entry, so sites must already
tolerate brands they do not recognize.

```json
"brands": [
  {"brand": "Chromium", "version": "147"},
  {"brand": "Not.A/Brand", "version": "8"},
  {"brand": "har-browse", "version": "1"}
]
```

## Measured safe against the aistudio gate

`Sec-CH-UA` might plausibly have gotten the same shape check the
`User-Agent` string does. It does not: a brand-list entry paired with
the shipped comment form passes (`../ua-position-gate.md`, last table,
row 12). Nothing about this channel is blocked by the constraint that
rules out a trailing product.

## The one thing to get right

The token must go into **both** `brands` and `fullVersionList`. If the
two lists disagree, that inconsistency is itself detectable — more so
than the disclosure it was meant to carry.

Worth knowing while implementing: Chromium's real list here is short and
its GREASE entry is not what upstream examples show. Measured on the
pinned revision, `brands` is `"Chromium";v="147", "Not.A/Brand";v="8"` —
two entries, no `"Google Chrome"`, because this is Chromium rather than
branded Chrome. Any code that assumes a three-entry list or a particular
GREASE spelling is assuming wrong.

## Cost to implement

Small. `userAgentMetadata()` already reads the browser's true metadata
and `hostSession()` already sends it, so this is an insertion into an
existing structure rather than new machinery.
