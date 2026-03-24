---
why:
  - toy-emit
  - deterministic-output
---

# M4 — Markdown Emission

Emitter produces deterministic markdown from extracted conversation data.

## Acceptance

- `toy_emit extracted.json --outdir output/` produces `branch-main.md` and
  `branch-alt.md`
- Output is byte-identical across runs
- Writes are atomic (staging directory → rename)
