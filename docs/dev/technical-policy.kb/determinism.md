---
force: should
source:
  - user (bukzor)
---

# Deterministic by Construction

Output is a pure function of durable input: no hysteresis (state carried
between runs), no oracles (an authority consulted at decision time).

Determinism is not stability: emit-order numbering is deterministic yet
renumbers everything when input grows. Where references must survive growth,
use append-stable handles — new items order strictly after all existing ones
(e.g. chronological rank), so existing handles never shift.

Canonical statement: `.claude/design-rules.kb/deterministic-by-construction.md`
in [bukzor/dotfiles](https://github.com/bukzor/dotfiles).
