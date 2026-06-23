---
status: contested
likelihood: 0.5
sources: [sources.kb/live-replay-probe.md]
tags: [aistudio, schema, rationale, doubt]
---

The browser bundle is the only available source of the MakerSuite schema —
the toolkit's motivating rationale. **Now contested.**

It holds only for a *formal schema document*: no descriptor, `.proto`, or
reflection is obtainable from the server (`claims.kb/no-grpc-reflection.md`).
But the operational goal was field **names + structure**, and the server hands
those over directly via `?alt=json`
(`claims.kb/alt-json-yields-named-projection.md`) — so the bundle is *not* the
only source of what the toolkit actually set out to recover. The motivation
survives only in the narrow descriptor sense, or where one must work purely
offline from a capture.

Conclusion of `deductions.kb/server-route-unavailable.md` (now undercut).
