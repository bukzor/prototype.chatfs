# Custom request header

**Verdict: unavailable. Not a policy result.**

An `X-Har-Browse` header carrying the tool name and contact URL is the
tidiest disclosure imaginable: it touches no fingerprint surface, needs
no grammar, and cannot be confused with a claim about what the browser
is.

It does not work. Page-context traffic to a cross-origin endpoint is
subject to CORS preflight, and a header the endpoint does not list in
`Access-Control-Allow-Headers` kills the request outright. Measured: the
probe's `X-Har-Browse` variant never reached the wire, failing at
preflight rather than being refused by the provider
(`../ua-position-gate.md`).

Worth distinguishing from the User-Agent results. The provider has no
opinion here; the browser's own security model forbids it. No provider
policy change would make this channel available, and only same-origin or
top-level-navigation traffic could carry one — which is not where the
interesting requests are.
