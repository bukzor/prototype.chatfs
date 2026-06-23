---
managed-by: Skill(llm-subtask)
---

# Tactical Tasks — aistudio-schema

Scope: the AI Studio schema-extraction toolkit in this directory. Discourse
graph at `discourse.kb/`.

## Offline decode

Live decode landed 2026-06-20 (commit 864686b): `?alt=json` returns the named
projection, so a live call with extracted auth decodes deterministically. The
open work is decoding *offline* from a capture, with no live auth.

The jspb→json reproducibility loop landed 2026-06-23 in `rosetta/` — five steps
(capture → correlate → convert → verify), gated offline by redo `rosetta/check`
against a committed golden pair. See README "Converting JSPB → JSON".

- [x] **Rosetta loop built** — `rosetta/{capture.sh,correlate.py,convert.py,
  verify.py}` + `check.do`. convert.py's hand-curated SCHEMA *is* the
  `slot → field-name` table; correlate.py derives/validates it from a golden
  pair (`resolvedrive.{jspb,alt-json}.json`); verify.py asserts the conversion
  is name/shape-equal to the real alt=json (bool/enum/timestamp value reprs
  tolerated). Green: verify passes, `redo all` passes, pyright clean.
- [x] **Alignment is NOT unambiguous from ordering alone** — partial answer to
  `discourse.kb/questions.kb/can-we-decode-deterministically.md`: the
  field-number ordering heuristic mis-assigns slots whenever a field is absent
  in the sample (the monotonic claim skips the null slot, e.g. `isMe` absent →
  `photoUri` claimed at slot 1, not 2). So the table stays hand-curated,
  cross-checked against `walk-graph.py` field numbers; correlate.py is an aid.
  - [ ] **Exercise stability across prompt types** (repeated, oneof,
    absent/optional) with more golden pairs — full resolution of
    `can-we-decode-deterministically.md`. Today: one golden pair only.
- [ ] **Confirm offline decode is the actual need** — blocked-soft on the
  purpose decision (`discourse.kb/questions.kb/how-does-this-serve-chatfs.md`,
  open). The loop validates *conversion*; wiring it to decode capture JSPB
  bodies offline waits on a named downstream consumer.
