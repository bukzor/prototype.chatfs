---
why:
  - validate-pipeline-shape
---

# Deterministic Output

Given the same conversation graph from the toy backend, the emitter produces
byte-identical markdown output across runs. Timestamps and UUIDs in the toy
data are fixed, not generated.

**Verification:** Run the full pipeline twice; `diff` the output directories.
