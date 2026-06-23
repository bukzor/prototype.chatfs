--- # workaround: anthropics/claude-code#13003
requires:
    - Skill(llm-discourse-graph)
---

# aistudio-schema discourse graph

Epistemic representation of the claims and assumptions behind the
AI Studio schema-extraction toolkit (`../`).

Most nodes are sourced from `sources.kb/readme.md` (high confidence).
Nodes whose likelihood is below 1.0 — or marked `contested` — are points
of genuine doubt: either the README hedges them, or they are the
assistant's inference rather than the README's assertion.

Entry points: `questions.kb/`.
