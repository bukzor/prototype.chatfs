--- # workaround: anthropics/claude-code#13003
depends:
  - Skill(llm-design-kb)
---

# chatfs-mockup-chatgpt — Design Knowledge

Decisions specific to this incubator that are worth persisting beyond the
current session. Mission/goals/requirements live in the parent
`docs/dev/design.kb/`; entries here link upward via `why:` where useful.

## Collections

- `040-design.kb/` — Decisions about pipeline shape, CLI surface, regeneration
  semantics, and the contract between browse and downstream stages.

The README at the incubator root covers what the mockup is *for*; this kb
covers *how it behaves* in ways that future sessions need to honor.
