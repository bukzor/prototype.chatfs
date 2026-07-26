# User-Agent trailing product

**Verdict: refused. Fallback only.**

The bot convention — `Googlebot/2.1 (+http://…/bot.html)` — appended
after the browser's last product:

```
Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) \
Chrome/147.0.0.0 Safari/537.36 har-browse/1.0.0 (+https://…)
```

Universally understood, and unusable against Google: measured 403,
`../ua-position-gate.md`. A neutral token in the same position is
refused identically, so no naming or decoration rescues it.

Retained as `brandUserAgent()`'s fallback for a User-Agent with no
comment to extend — identifying in a refused position beats not
identifying at all — which real Chromium never triggers.

Elaborations of this channel keep getting proposed and all inherit the
403: a second product for the enclosing project
(`prototype-chatfs/0.1 har-browse/1.0.0 (+URL)`), the same wrapped in a
descriptive comment (`prototype-chatfs/0.1 (scripted via
har-browse/1.0.0; +URL)`), a bare disposition token
(`har-browse/1.0.0 attended`). The gate does not read them.

## Grammar

As an RFC 9110 `product`, the name and version must both be `token`s.
`;` and `:` are not token characters, so the contact URL needs a
`comment` of its own out here. That is a *different spelling* from the
system-information-comment channel's, and conflating the two produced an
ungrammatical User-Agent once already; `tests/brand_user_agent.test.mjs`
now parses both against the ABNF.
