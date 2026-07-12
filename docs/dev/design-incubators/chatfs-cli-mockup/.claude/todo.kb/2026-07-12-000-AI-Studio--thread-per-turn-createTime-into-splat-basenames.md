---
managed-by: Skill(llm-subtask)
cost-benefit-sweh:
  timebox:
    "@value": 0.75
    rationale: >
      Small, well-understood change: thread an already-available field into
      basename generation, update tests. No design question — deferred only
      because it wasn't required to fix the splat crash it was found next to.
    confidence: tentative
  benefit-2w:
    "@value": 0.3
    rationale: >
      Closes a known cosmetic gap (render-time timezone dependency for AI
      Studio headings, accepted as low-priority 2026-07-11) but nothing is
      broken today; chat.md is gitignored/regenerated freely.
    confidence: tentative
---

# AI Studio: thread per-turn createTime into splat basenames

**Priority:** Low — deferred scope, not a live bug.
**Complexity:** Low
**Context:** Extracted 2026-07-12 from
`todo.kb/2026-07-03-000-cross-provider-data-flow-drift--pre-unification-fixes-vs-unification-scope.md`
(deleted after this promotion) § "Fix before unification" item 1's nested
sub-item, found while retargeting `chatfs_aistudio_conversation_splat.py` to
the massaged doc — see devlog
`2026-07-03-000-chatfs-mockup-chatgpt-aistudio-massage-json-and-url-browse.md`.
Related: devlog
`2026-07-11-001-aistudio-conversation-render-linear-chain.md`'s "Open
questions" note on render-time timezone dependency (same underlying gap,
accepted as-is for now).

## Problem Statement

Claude and chatgpt bake a local-time-with-offset timestamp into each
message's filename once, at splat time. AI Studio's splat does not — its
per-turn basenames are index-only. As a result,
`chatfs_aistudio_conversation_render.py` computes heading timestamps at
*render* time instead (epoch seconds → local wall clock via
`.astimezone()`), so re-rendering `chat.md` on a machine in a different
timezone than the original capture shows a different wall-clock hour for
AI Studio only — the other two providers are stable under this because the
offset is already baked into the filename.

## Current Situation

The chunk's `createTime` field is confirmed present in the massaged JSPB
doc (verified live, 2026-07-03) but unused by splat's basename generation.
Two turns (e.g. a user turn and its thought) can share an identical
`createTime`, so the existing index component in the basename must be kept
alongside any new timestamp component — it is still needed for ordering.

## Proposed Solution

Thread `chunk.createTime` into `chatfs_aistudio_conversation_splat.py`'s
per-turn basename generation, following claude/chatgpt's
local-time-with-offset convention, while retaining the index component for
tie-breaking. Update `chatfs_aistudio_conversation_render.py` to read the
timestamp from the filename (splat-time-baked) rather than computing it at
render time, matching the other two providers' architecture.

## Implementation Steps

- [ ] Add `createTime`-derived local-time-with-offset component to
      `chatfs_aistudio_conversation_splat.py`'s basename generation,
      keeping the index component for same-timestamp tie-breaking.
- [ ] Update `chatfs_aistudio_conversation_render.py` to read the baked
      timestamp from the filename instead of computing it at render time
      from epoch seconds.
- [ ] Update/extend `chatfs_aistudio_conversation_render_test.py` and any
      splat tests to cover the new basename shape.
- [ ] Verify end-to-end against the demo capture: `chat.md` output
      unchanged in content, basenames now timestamp-bearing.

## Open Questions

- None — this is implementation, not design. (Contrast with the
  deliberately unscheduled `turn_kind()`/reasoning-turn-mapping items in
  the AI Studio parity ladder, which do have open design questions.)

## Success Criteria

- [ ] AI Studio per-turn basenames carry a local-time-with-offset
      component, mirroring claude/chatgpt.
- [ ] `chat.md` heading timestamps are stable across renders regardless of
      the rendering machine's timezone.
- [ ] `basedpyright .` 0/0/0; full test suite passes.

## Notes

Not blocking, not scheduled — carried forward from the drift file's
deferred scope. Pick up whenever AI Studio work is next active.
