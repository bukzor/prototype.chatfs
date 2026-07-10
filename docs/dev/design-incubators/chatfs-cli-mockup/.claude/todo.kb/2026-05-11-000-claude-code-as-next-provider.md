---
managed-by: Skill(llm-subtask)
cost-benefit-sweh:
  timebox:
    '@value': 4
    confidence: tentative
    rationale: |
      Third provider; local-files datasource (no BB1). Design open questions: locator shape, per-turn richness for tool calls/sub-agents/hooks, provider naming. Implementation after design: extractor reading ~/.claude/, locator parser, noun-verb extension. ~3-5 SWEh once unblocked.
  benefit-2w:
    '@value': 1
    confidence: tentative
    rationale: |
      Third provider unlocks rule-of-three signal for the shared-code refactor (sibling todo). Within 2w mostly design clarity not landing — claude.ai parity is the trigger and not yet done.
  cost-of-delay-2w:
    '@value': 0.1
    confidence: tentative
    rationale: |
      Gated on claude.ai parity. Each 2w of delay defers the rule-of-three test; small option value on earlier shared-lib design clarity.
---

# claude-code as next provider (datasource `~/.claude`)

**Priority:** Low (sequenced after the claude.ai parity ladder)
**Complexity:** Low–Medium structurally — no BB1 (no browser capture);
local-files datasource. Risk concentrates in modeling claude-code's
richer per-turn structure (tool calls, sub-agents, hooks).

**Context:**
- User note (2026-05-11): *"after claude.ai we add support for
  (localhost) claude-code, where the datasource is rather `~/.claude`,
  but the resulting chatfs is very similar."*
- `../../design.kb/040-design.kb/black-box-decomposition.md` — BB1 is
  optional for this provider (filesystem read replaces browser
  capture).
- `../../design.kb/040-design.kb/cli-command-shape.kb/` — noun-verb
  command shape must extend to a non-URL locator.

## Scope

Add a third provider whose extractor reads `~/.claude/` directly.
Rendered chatfs view (chat-as-directory, `messages/<stem>.md`,
`chat.md`, `.data/`) stays the same shape as chatgpt and claude.ai.

## Open Questions

- **Locator:** project + session-id, absolute session-file path, or
  both?
- **Per-turn richness:** tool calls, sub-agent invocations, hook
  output — do they fit `messages/<stem>.md` cleanly, or does
  claude-code want a richer view?
- **Provider name:** `claudecode` collides visually with `claudeai`.
  Decide before scripts are named.
- **Sequence:** strictly after claude.ai, or could it leapfrog?
  (claude-code has no auth dance, no browser — fastest path to a
  second working provider, at the cost of less BB1 reuse signal.)

## Notes

Implementation deferred — scope and design pending claude.ai parity
landing (which crystallizes the noun-verb extension points).
