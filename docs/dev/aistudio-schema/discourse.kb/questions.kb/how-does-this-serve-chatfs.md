---
candidate-resolutions: [claims.kb/purpose-feeds-bb2-extraction.md]
tags: [chatfs, bb2, doubt]
status: resolved
resolved: 2026-07-03
---

What role does the recovered AI Studio schema play in chatfs as a whole? The
README explains *how* the toolkit works and *why* the bundle approach is
necessary, but never names a downstream consumer.

**Resolved 2026-07-03.** A named consumer now exists:
`../../design-incubators/chatfs-mockup-chatgpt/chatfs_aistudio_conversation_massage_json.py`.
It's a *port*, not an import — this package stays exploratory/disposable per
the user, so the mockup pipeline owns its own copy of `rosetta/convert.py`'s
`SCHEMA` (verified against `rosetta/resolvedrive.alt-json.json` while
porting: two bugs surfaced and were fixed — a dropped `"prompt"` top-level
wrapper, and a weakened `Literal["map"]` type). The mockup's
`chatfs_aistudio_conversation_url_browse.py` calls it to turn a captured
`ResolveDriveResource` body into `conversation.json`, live-tested end-to-end.
This confirms `purpose-feeds-bb2-extraction.md`'s candidate resolution: the
schema's role is feeding the chatfs pipeline's JSPB decode, by way of a
hand-ported (not imported) copy.
