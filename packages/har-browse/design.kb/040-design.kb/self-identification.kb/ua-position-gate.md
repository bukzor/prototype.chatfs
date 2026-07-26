---
why:
  - unblocked-sessions
---

# The User-Agent gate is positional

Google refuses aistudio's `GenerateContent` — `PERMISSION_DENIED`, while
every other RPC on the same service succeeds with the same credentials —
whenever **anything trails the browser's product list**. A neutral
`Foo/1.0` is refused exactly as our own name is, so the check is on the
User-Agent's *shape*, not on who we say we are. Nor is it a consistency
check against the client hints: declaring the same token in `Sec-CH-UA`
does not rescue the position (see below).

The same identity placed inside the system-information comment is
accepted, contact URL and all.

## The grammar this is about

RFC 9110 §10.1.5: `User-Agent = product *( RWS ( product / comment ) )`.
Chromium's UA is six elements —

```
Mozilla/5.0                     product
(X11; Linux x86_64)             comment    <-- system information
AppleWebKit/537.36              product
(KHTML, like Gecko)             comment
Chrome/147.0.0.0                product
Safari/537.36                   product
```

— and the gate cares only about whether element 6 is the last one. Both
positions are grammatical; they differ in what they *assert*. A trailing
product claims to be another layer in the user-agent stack. A field in
the system-information comment claims to be a property of the
environment the browser runs in, which is what a capture harness
actually is.

## Measured 2026-07-26

The sibling `ua-position-gate.mjs`, aistudio `GenerateContent`, one
live session, control first. Every row is the full Chromium UA with the
stated edit; the table is the script's own summary output, pasted.

| edit | `Sec-CH-UA` | result |
| --- | --- | --- |
| none (control) | absent | 200 |
| `+ har-browse/1.0.0 (+URL)` after `Safari/537.36` | absent | 403 |
| `+ har-browse/1.0.0` after `Safari/537.36` | absent | 403 |
| `+ har-browse` after `Safari/537.36` | absent | 403 |
| `+ Foo/1.0` after `Safari/537.36` | absent | 403 |
| `(X11; Linux x86_64; har-browse/1.0.0)` | absent | 200 |
| `(X11; Linux x86_64; har-browse/1.0.0; +URL)` | absent | 200 |
| control UA, disclosure in an `X-Har-Browse` header | absent | did not reach the wire |
| none (control) | truthful | 200 |
| `+ har-browse/1.0.0` after `Safari/537.36` | truthful | 403 |
| `+ har-browse/1.0.0` after `Safari/537.36` | truthful + `har-browse;v=1` | 403 |
| `(X11; Linux x86_64; har-browse/1.0.0; +URL)` | truthful + `har-browse;v=1` | 200 |
| none (control), re-check | absent | 200 |

Rows 2–5 establish the *class*: any proposal that puts a product after
`Safari/537.36` inherits the 403, whatever it is named or decorated
with. Specific proposals so eliminated are recorded in the channel they
would modify, under `disclosure-surfaces.kb/`.

The `X-Har-Browse` row is not a policy result: the custom header is not
in the endpoint's `Access-Control-Allow-Headers`, so preflight kills the
request and the provider never sees it. Header-borne disclosure is
unavailable to page-context traffic regardless of what the provider
would think of it.

The last row is a re-check of the first. Thirteen real generations in a
row can draw rate limiting, which reads as a refusal and would poison
every 403 above it; the control still passing at the end is what makes
the run admissible.

## Shape, not coherence

The obvious rival hypothesis: the refusals are not shape validation but
UA/client-hint *coherence* checking — a UA claiming an extra product
while `Sec-CH-UA` says plain Chrome is an inconsistency, and that
inconsistency, not the position, is what gets caught. It matters,
because if true a trailing product would be rehabilitated by declaring
the same token in the brand list, and the conventional bot spelling
would be available to us after all.

The last five rows settle it. Two variables, separated:

- **Are hints read at all?** Control passes with them absent (row 1) and
  with them truthful (row 9). The trailing product fails both ways (rows
  3 and 10). Hint presence changes nothing on this endpoint.
- **Does coherence rescue the position?** Row 11 declares
  `"har-browse";v="1"` in the brand list alongside the same trailing
  product, so UA and client hints agree exactly. Still 403.

The gate reads the User-Agent string. Making the client hints corroborate
the edit does not soften it, which also means the hint metadata cannot be
what triggers it.

Row 12 is the useful surprise: the brand-list entry paired with the
shipped comment form passes. Disclosure in `Sec-CH-UA` is compatible with
this gate — see `disclosure-surfaces.kb/sec-ch-ua-brand-list.md`.

## Not yet measured

- Whether other providers (claude.ai) react to the comment field at all.
  No reason to expect trouble; never checked.
- Whether the gate is Google-wide or aistudio-specific.

## Consequence

`brandUserAgent()` in `src/host_puppeteer.mjs` extends the
system-information comment. `tests/brand_user_agent.test.mjs` holds the
shape by parsing the result against the ABNF above;
`tests/user_agent_client_hints.spec.mjs` asserts end-to-end that nothing
trails the product list.
