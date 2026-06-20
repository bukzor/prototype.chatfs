---
anthropic-skill-ownership: llm-subtask
cost-benefit-sweh:
  timebox:
    '@value': 4
    confidence: tentative
    rationale: |
      Two of ~8 rungs landed (pluck + splat). Remaining: index
      pluck/splat, conversation_render, path_render, url/path browse,
      url_render, browse automation. JSPB positional decoding is the
      novel cost vs chatgpt/claude (keyed JSON); the orchestration
      rungs should mirror the claude side closely. ~3-5 SWEh.
  benefit-2w:
    '@value': 1
    confidence: tentative
    rationale: |
      A third provider — and the first non-keyed (JSPB) source — is
      the strongest signal yet for the shared-lib extraction. Closing
      the ladder both delivers AI Studio and de-risks chatfs-core.
---

# AI Studio provider parity ladder

**Priority:** Medium — third provider; first JSPB source.
**Complexity:** Medium — orchestration mirrors claude; the new cost is
JSPB positional decoding (see `dev.kb/claims.kb/aistudio-jspb-prompt-shape.md`).

## Landed this session (2026-06-20)

- [x] `chatfs_aistudio_conversation_pluck.jq` — select the
      `ResolveDriveResource` body, guard on `[0][0] == "prompts/<id>"`,
      `fromjson`. Output: one conversation doc/line, same kind as the
      chatgpt/claude pluck.
- [x] `chatfs_aistudio_conversation_splat.py` — walk `[0][13][0]` turns,
      classify user/answer/thought from `[8]`/`[16]`/`[19]`, write
      `<src>.splat/messages/NNN.{role}[.thought].{json,md}`; thoughts as
      `<details type="thinking">` (lifts + dedups the `**bold**` header).

## Remaining rungs (mirror the claude ladder)

- [ ] `chatfs_aistudio_index_pluck.jq` + `chatfs_aistudio_index_splat.py`
      — needs an index capture (likely `ListPrompts`; not yet reverse-
      engineered, unlike the conversation body).
- [ ] `chatfs_aistudio_conversation_render.py` — AI Studio prompts are
      **linear** (a flat turn list, no fork tree observed), so render is
      simpler than claude's DFS — but confirm forks truly can't exist
      before assuming it.
- [ ] `chatfs_aistudio_conversation_path_render.py` — orchestrator
      (splat → move up → render `chat.md`).
- [ ] `chatfs_aistudio_conversation_url_browse.py` /
      `..._path_browse.py` / `..._url_render.py` — entry points.
- [ ] Browse automation (`..._index_browse.sh`) once index pluck exists.

## Design questions surfaced

- [ ] Decide where **reasoning** lands in the canonical conversation
      graph. The graph has no reasoning slot, and the three providers
      shape it three ways — see
      `dev.kb/claims.kb/reasoning-turn-mapping-differs-by-provider.md`
      and the gap note in
      `../../../../design.kb/040-design.kb/canonical-conversation-graph.md`.
      A uniform "one response = one unit" view must be synthesized in
      BB2/BB3.

## Notes

- All field indices are from a **single** capture (`status: observed`).
  A second prompt — especially one with images, multiple parts, or any
  fork — may refute the 36-field turn width or the 1:1 thought↔answer
  ratio.
- AI Studio is a third *browser-captured* provider. This strengthens
  the shared-lib signal earlier than the claude-code trigger assumed in
  `2026-05-11-001-shared-code-among-providers.md`; revisit that entry's
  rule-of-three argument once this ladder progresses.
