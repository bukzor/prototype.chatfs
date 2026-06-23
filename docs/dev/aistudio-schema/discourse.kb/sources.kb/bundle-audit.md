---
kind: investigation
title: "Bundle audit — grep/walk over bundles/*.js (2026-06-22)"
tags: [aistudio, schema, audit, primary]
---

Direct inspection of the seven captured bundles and `accessors.jsonl`, run
while evaluating this graph. Primary evidence (the artifacts themselves), not
the README's report of them.

Findings:

- **140 accessors, 13 distinct primitives.** Only 4 are in the README legend
  (`_.l` 56, `_.X` 18, `_.xi` 5, `_.Mj` 1 = 80 rows). The other 9 primitives
  (`_.sm` 22, `_.tm` 12, `_.Do` 8, `_.An` 6, `_.Qi` 6, `_.jp` 2, `_.Ii` 2,
  `_.Lm` 1, `_.Or` 1 = 60 rows) are un-typed. **Legend coverage ≈ 57 %.**
- **RPC stub verified.** `_b.js:42772` lists the `ResolveDriveResource` path,
  then `_.h9a` (request), then `i9a` (response) — confirming `i9a` is the
  response ctor exactly as the README's usage comment implied.
- **The conversation rides in `ResolveDriveResource` — but its turns have no
  getter.** Decoding the real payload (via `chatfs_aistudio_conversation_pluck.jq`)
  shows the response Prompt object has many positional slots: idx0 = Name
  (`prompts/<id>`), idx4 = Metadata (DisplayName = the title), and a later slot
  = the **turns array** (text + `"user"`/model roles + timestamps). Yet the
  response ctor `_.Qw` defines only `getName` and `getMetadata`. So getter-based
  recovery surfaces ~2 of ~14+ fields; the turns field is invisible to the walk.
  Generated accessors exist only for fields the app reads via accessor — the
  method recovers a skeleton, not the whole message.
- **Decode validates the recovered numbers (for getter-exposed fields).** In the
  real payload, Name lands at idx0, Metadata at idx4, DisplayName at idx0 of
  Metadata — exactly as the accessors say. Positive cross-check.
- **Only conversation-shaped getters anywhere:** `getContentWorker`,
  `getMessage`, `getText` — no `getRole`/`getTurn`/`getAuthor`/`getPart`. The
  turn submessage's getters are either in an un-captured module or absent.
  Correction to an earlier reading: `ResolveDriveResource` is NOT merely a
  Drive-metadata lookup; it is the conversation-bearing RPC.
- **`accessors.jsonl` has no owning-message field.** It is a flat bag of
  `{name, number, prim, submsg}`; message membership exists only transiently
  inside `walk-graph.py`. Two distinct `#1` fields (`Type`, `Name`) sit
  adjacent with nothing to disambiguate their owners.
