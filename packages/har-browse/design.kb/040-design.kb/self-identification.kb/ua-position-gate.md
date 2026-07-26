---
why:
  - unblocked-sessions
---

# The User-Agent gate is positional

Google refuses aistudio's `GenerateContent` — `PERMISSION_DENIED`, while
every other RPC on the same service succeeds with the same credentials —
whenever **anything trails the browser's product list**. A neutral
`Foo/1.0` is refused exactly as our own name is, so the check is on the
User-Agent's *shape*, not on who we say we are.

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

| edit | result |
| --- | --- |
| none (control) | 200 |
| `+ har-browse/1.0.0 (+URL)` after `Safari/537.36` | 403 |
| `+ har-browse/1.0.0` after `Safari/537.36` | 403 |
| `+ har-browse` after `Safari/537.36` | 403 |
| `+ Foo/1.0` after `Safari/537.36` | 403 |
| `(X11; Linux x86_64; har-browse/1.0.0)` | 200 |
| `(X11; Linux x86_64; har-browse/1.0.0; +URL)` | 200 |
| control UA, disclosure in an `X-Har-Browse` header | did not reach the wire |

The last row is not a policy result: the custom header is not in the
endpoint's `Access-Control-Allow-Headers`, so preflight kills the
request and the provider never sees it. Header-borne disclosure is
unavailable to page-context traffic regardless of what the provider
would think of it.

### Caveat on method

The probe sends `Network.setUserAgentOverride` without
`userAgentMetadata`, which strips all `Sec-CH-UA*` headers. Every row
above, control included, ran with client hints absent. The control's 200
shows hints are not gated on this endpoint, so the positional conclusion
stands — but the probe does not reproduce the shipped configuration, and
must be fixed to pass truthful metadata before it can measure anything
about the hints themselves.

The four rows in the middle establish the *class*: any proposal that
puts a product after `Safari/537.36` inherits the 403, whatever it is
named or decorated with. Specific proposals so eliminated are recorded
in the channel they would modify, under `disclosure-surfaces.kb/`.

## Not yet measured

- Whether other providers (claude.ai) react to the comment field at all.
  No reason to expect trouble; never checked.
- Whether the gate is Google-wide or aistudio-specific.
- `Sec-CH-UA` brand-list disclosure — see `disclosure-surfaces.md`.

## Consequence

`brandUserAgent()` in `src/host_puppeteer.mjs` extends the
system-information comment. `tests/brand_user_agent.test.mjs` holds the
shape by parsing the result against the ABNF above;
`tests/user_agent_client_hints.spec.mjs` asserts end-to-end that nothing
trails the product list.
