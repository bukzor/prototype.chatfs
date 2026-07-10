--- # workaround: anthropics/claude-code#13003
depends:
  - Skill(llm-kb)
---

# dev.kb — working knowledge from dev sessions

Distinct from `design.kb/` (durable design rationale, layered mission →
goals → requirements → design → future work). `dev.kb/` is the
ephemeral-but-cite-able layer: things observed, learned, or corrected
during work that aren't yet design decisions but shouldn't get lost in
devlog narrative.

Two sub-collections by type:

- `claims.kb/` — empirical assertions about external behavior, tools,
  or data shapes. Each has `status:` (`assumed` / `observed` /
  `refuted` / `settled`). Corrections of prior bad versions fold in
  via the optional `previously-claimed:` schema field on the affected
  claim — no separate clarifications collection.
- `learnings.kb/` — durable insights about the codebase, design, or
  process. Each is a non-obvious fact a future agent should know.
  No status; stable. Prose-only.

When an item stabilizes (claim settled; learning becomes load-bearing
for a design decision), consider promoting it into `design.kb/` or
into the relevant tactical todo.
