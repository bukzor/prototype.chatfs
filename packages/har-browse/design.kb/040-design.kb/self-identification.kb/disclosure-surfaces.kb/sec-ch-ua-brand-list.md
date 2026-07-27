# Sec-CH-UA brand list

**Verdict: shipped.**

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

## Position

Appended, and the GREASE entry is left wherever the browser put it.
Nothing requires GREASE to be last: Chromium's `GenerateBrandVersionList`
picks from a 3! permutation table seeded by the major version, so the
order is fixed per release and varies across them — real captures show
GREASE leading (`"Not/A)Brand";v="99", "Microsoft Edge";v="115", …`) as
readily as trailing. Position carries no meaning by construction, which
is the whole point of GREASEing the list.

Appending does have one concrete virtue: the browser's own entries stay
contiguous and in their original order, so a comparison against a known
profile for this Chromium sees one clean addition at the end rather than
a shift through the middle.

## Implementation

`userAgentMetadata()` in `src/host_puppeteer.mjs`, which was already
reading the browser's true metadata for `hostSession()` to send — this
is an insertion into an existing structure, not new machinery.

`tests/user_agent_client_hints.spec.mjs` holds it against the wire
headers, and asserts the parsed lists rather than substrings: our entry
appears exactly once, at the end, with the right version in each list,
and the browser's own brands survive ahead of it unchanged. The oracle
for "unchanged" is a second, untouched puppeteer launch. It must be
puppeteer: Playwright *headless* runs a different executable and reports
a three-entry list led by `"HeadlessChrome"` (see
`../headless-changes-the-agent.md`). The fixture's `/client-hints` route
sends `Accept-CH` so the negotiated full-version list actually appears on
the wire; without it, half of this ships untested.
