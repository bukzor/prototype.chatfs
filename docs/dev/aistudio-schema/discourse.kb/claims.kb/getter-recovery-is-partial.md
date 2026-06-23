---
status: asserted
likelihood: 0.95
sources: [sources.kb/bundle-audit.md]
tags: [aistudio, schema, coverage, doubt]
---

Getter-based schema recovery is **partial per message**: it surfaces only the
fields the app reads through generated accessors, not every field on the wire.

The decisive case is the conversation itself. `ResolveDriveResource` carries the
full prompt — turns, roles, content, timestamps all ride in its response
(confirmed by decoding a real payload, and by the working
`chatfs_aistudio_conversation_pluck.jq`). But the response ctor `_.Qw` defines
exactly two getters, `getName` (idx0) and `getMetadata` (idx4); the turns array
sits at a later JSPB slot with **no accessor in these bundles**. So `walk-graph`
recovers ~2 of the Prompt message's ~14+ fields and stops before the content.

**Consequence for the enterprise.** The turn/role/content field numbers — the
ones an extractor actually needs — are *not* recovered by this method from this
capture. Closing the gap requires either the module that defines the turn
submessage's getters (a wider re-capture), or positional reverse-engineering
straight from payloads — which is exactly what the `.jq` already does, bypassing
the toolkit's recovered numbers entirely.
