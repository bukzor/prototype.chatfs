---
status: asserted
likelihood: 1.0
sources: [sources.kb/readme.md, sources.kb/live-replay-probe.md]
tags: [aistudio, rpc]
---

The `$rpc` front end exposes no gRPC reflection and no discovery document, so a
formal **schema** (descriptor / `.proto`) cannot be obtained from the server.
Now verified empirically: live probes of reflection (400), `/$discovery/rest`
(404), and `/discovery/v1/apis` (404) all fail.

Scope: this is about a schema *document*. The server is not otherwise opaque —
it returns named field *data* via `?alt=json`
(`claims.kb/alt-json-yields-named-projection.md`), and leaks *request* field
names + proto types through structured `google.rpc.BadRequest` errors when sent
wrong-typed values.
