---
candidate-resolutions:
  - claims.kb/alt-json-yields-named-projection.md
  - claims.kb/offline-decode-needs-curation.md
depends: [claims.kb/field-names-absent-client-side.md]
tags: [aistudio, decode, goal, doubt]
---

Can an AI Studio conversation be decoded into fully-named fields
deterministically, without reverse engineering — and ideally offline from a
capture, without out-of-band auth?

**Open / partly answered.**
- *Live:* yes — `?alt=json` returns the named projection
  (`claims.kb/alt-json-yields-named-projection.md`). But it needs a live call
  with extracted auth, which the user wants to avoid as a routine path.
- *Offline from a capture:* no, not directly — the field names are absent
  client-side (`claims.kb/field-names-absent-client-side.md`).

The Rosetta path was tried (2026-06-23, `sources.kb/rosetta-correlation-experiment.md`):
fetch one prompt as both JSPB and `?alt=json`, align to derive a static
position→name map, then decode offline forever. The finding splits the question:

- *Deterministic per-decode:* **yes** — once a curated `slot → field` map exists,
  decoding any captured JSPB is mechanical (`rosetta/convert.py`).
- *Without reverse engineering:* **no** — positional alignment alone is
  ambiguous wherever a field is absent from the sample
  (`claims.kb/ordering-alignment-is-ambiguous.md`), so the map must be curated
  and cross-checked against the bundle (`claims.kb/offline-decode-needs-curation.md`).

So the offline goal is met in practice, at the cost of a one-time RE pass; the
"no RE" form is refuted for the alignment-only approach. Still untested:
stability across prompt types (repeated fields, oneofs, more absent/optional
slots) — only one golden pair exercised so far, so the question stays **open**.
