---
candidate-resolutions: [claims.kb/alt-json-yields-named-projection.md]
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

The open candidate is a **one-time Rosetta alignment**: fetch one prompt as both
JSPB and `?alt=json`, align position-by-position to derive a static
position→name map, then decode any captured JSPB offline forever. Unproven —
whether the alignment is unambiguous and stable across prompt types (repeated
fields, oneofs, absent/optional slots) is untested. Until then the goal stays
open.
