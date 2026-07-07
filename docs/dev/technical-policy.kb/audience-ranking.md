---
force: should
source:
  - user (bukzor)
---

# Audience Ranking: LLM, Plaintext Editor, Browser

Rendered artifacts and docs serve their consumers in this rank order:

1. LLM agents — grep windows, partial reads, token cost
2. Humans in plaintext editors
3. Humans in browser-rendered views

Lower ranks are real votes — good tie-breakers and design-space-search
heuristics — but never outvote a higher rank. State trade-offs against this
ranking positively (which rank wins and why), not as negative asides about
the losing rank.
