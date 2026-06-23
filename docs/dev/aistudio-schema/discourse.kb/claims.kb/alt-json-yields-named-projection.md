---
status: asserted
likelihood: 0.95
sources: [sources.kb/live-replay-probe.md]
tags: [aistudio, schema, live, decode]
---

Appending `?alt=json` to a MakerSuite `$rpc` call makes the server return
proto3 JSON keyed by **field name** instead of positional JSPB — a complete,
deterministic decode with no reverse engineering. Verified on
`ResolveDriveResource`: the response carries the whole conversation with named
fields down to the turns (`prompt.chunkedPrompt.chunks[].role/.text/
.parts[].thought`, `runSettings.*`, `metadata.*`).

**This is a finding, not the resolved goal.** It requires a *live* call with
out-of-band auth (cookie + SAPISIDHASH), which is undesirable as a routine
extraction path. Its value is analytic: it names the fields the captured
positional JSPB encodes. Uncertainty (<1.0): only one prompt was exercised;
whether the named projection is stable and complete across other prompt types
and the streaming RPCs is untested.
