--- # workaround: anthropics/claude-code#13003
depends:
  - Skill(llm-design-kb)
---

# chatfs Design Knowledge

Layered design documentation for the chatfs project. Each layer justifies
the one below via `why:` frontmatter links.

## Collections

- `010-mission.kb/` — What problem are we solving? Who benefits?
- `020-goals.kb/` — How do we accomplish the mission?
- `030-requirements.kb/` — How do we validate goals are achieved?
- `040-design.kb/` — How do we satisfy requirements?
- `070-future-work.kb/` — Good ideas not worth pursuing now

## Related

- `../background.kb/` — Domain concepts, technology primers, prior art
- `../technical-policy.kb/` — Cross-cutting normative guidance
