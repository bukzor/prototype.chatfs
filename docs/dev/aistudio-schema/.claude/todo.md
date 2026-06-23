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

- [ ] **Rosetta map generator** — fetch one prompt as both encodings via
  `curl-aistudio` (positional JSPB, and `?alt=json` named), align by matching
  leaf values → emit a static `index-path → field-name` table, then decode
  captured JSPB bodies offline. Distinct component from the fetcher
  (`curl-aistudio`) and the JSPB→JSON decoder.
  - [ ] **Confirm offline decode is the actual need** — blocked-soft on the
    purpose decision (`discourse.kb/questions.kb/how-does-this-serve-chatfs.md`,
    open). Build only once a downstream consumer is named.
  - [ ] **Prove the alignment is unambiguous and stable** across prompt types
    (repeated fields, oneofs, absent/optional slots). Resolves
    `discourse.kb/questions.kb/can-we-decode-deterministically.md` (open).
