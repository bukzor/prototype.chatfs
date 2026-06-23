---
kind: investigation
title: "Live API replay + introspection probe (2026-06-22)"
tags: [aistudio, rpc, live, primary]
---

Replaying the captured `ResolveDriveResource` request against
`alkalimakersuite-pa.clients6.google.com` with the user's own (fresh) auth —
cookie jar + SAPISIDHASH + reconstructed `Origin` — and probing the endpoint for
schema introspection. Tooling: `../live-replay.sh`. The user authorized use of
their own tokens against their own data.

Results:

- **Auth replay works** (HTTP 200) once `Origin: https://aistudio.google.com`
  is supplied; CDP records it only in `requestWillBeSentExtraInfo`.
- **`?alt=json` returns fully-named proto3 JSON** (HTTP 200,
  `application/json`) — including the conversation turns
  (`prompt.chunkedPrompt.chunks[].role/.text/.parts[].thought/...`). The `$rpc`
  path with `Content-Type: application/json` is rejected (400); only the
  `?alt=json` query param flips the encoding.
- **No formal schema document.** Discovery docs (`/$discovery/rest` → 404,
  `/discovery/v1/apis` → 404) and gRPC reflection (400) are absent.
- **But request fields DO leak via errors.** A wrong-typed value returns a
  structured `google.rpc.BadRequest` naming the field and proto type — e.g.
  `["resource_id", "Invalid value at 'resource_id' (TYPE_STRING), 12345"]`. So
  the *request* schema is recoverable field-by-field by sending bad values
  (with `Accept: */*`; an explicit `application/json` Accept gets an opaque HTML
  400 instead). Response/turn field names do not leak this way.

Single prompt tested; coverage across other prompt types / streaming RPCs not
yet exercised.
