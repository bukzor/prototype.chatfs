---
managed-by: Skill(llm-subtask)
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

## Landed 2026-06-22

- [x] `chatfs_aistudio_types.py` — `IndexItem` TypedDict (id/title/
      create_time), synthesized rather than passed through (JSPB has no
      native keyed dict to echo).
- [x] `chatfs_aistudio_layout.py` — mirrors `chatfs_chatgpt_layout.py` /
      `chatfs_claude_layout.py`: `index_item()` reads the identity fields
      out of the positional prompt doc by index (`PROMPT`/`META`/`TITLE`/
      `CREATED`), `place_meta()` is byte-for-byte the chatgpt path once
      synthesis happens. Prep work for the index rung below — no
      `chatfs_aistudio_index_splat.py` yet, since that needs the index
      capture first.

## Landed 2026-07-03

- [x] `chatfs_aistudio_conversation_massage_json.py` — JSPB → named JSON,
      schema ported (not imported) from `../aistudio-schema/rosetta/convert.py`
      and fixed against its golden pair while porting: restored the `"prompt"`
      top-level wrapper (verified against `resolvedrive.alt-json.json`, the
      real ground truth) and `Literal["map"]` type precision, both lost in
      the first draft. Emits the *whole* named document — no re-narrowing to
      a subset (e.g. just turns) — mirroring what chatgpt/claude get for free
      from their already-keyed wire format. This is the "named downstream
      consumer" `aistudio-schema`'s own todo was blocked on.
- [x] `chatfs_aistudio_conversation_url_browse.py` — capture → pluck →
      massage → place_meta, entry point by URL (`/prompts/<id>`). Simpler
      than chatgpt/claude's url_browse: no incidental-index cross-check,
      since identity (`metadata.displayName`/`lastModified`) arrives in the
      *same* `ResolveDriveResource` body that becomes `conversation.json` —
      no second endpoint to reconcile against. Live-tested end-to-end
      against the real prompt (`1vU6BlpV69d2MvI6L_oYGo_E-ZqmaI3eR`); writes
      `cdp.jsonl` + `conversation.raw.json` + `conversation.json` +
      `meta.json` + view symlink, all verified correct.
- [x] New naming convention (documented in
      `design.kb/040-design.kb/cli-command-shape.kb/noun=conversation.kb/verb=browse.md`):
      `conversation.raw.json` (plucked JSPB, for audit) vs. `conversation.json`
      (named, massage's output) — a split unique to AI Studio; chatgpt/claude
      have no `.raw.json` since pluck's output is already "good."

## Landed 2026-07-11

- [x] `chatfs_aistudio_index_pluck.jq` + `chatfs_aistudio_index_splat.py`
      + `chatfs_aistudio_index_browse.sh` — the index rung (consumes
      `chatfs_aistudio_layout.index_item` + `place_meta`, landed
      2026-06-22). Index endpoint confirmed as `ListPrompts` (fires from
      `/library` and any `/prompts/<id>` page alike), reusing
      `ResolveDriveResource`'s PROMPT/METADATA schema unchanged — pluck
      now flattens either RPC's response to one prompt-message per line
      (`.[]`/`.[0][]`), and `massage_json`/`index_splat` share the same
      `PROMPT` projection regardless of which endpoint supplied the
      message (see devlog). Reverse-engineering this endpoint surfaced a
      real bug: `index_item()`/`IndexItem` assumed `create_time` from
      the first chunk's `createTime`, unavailable on a `ListPrompts`
      entry (no turn content) — fixed, `create_time` is `NotRequired`
      with an honest always-present `last_modified` alongside it (see
      `no-partial-synthesis.md`). Live-tested against this account's 42
      prompts (one `ListPrompts` page, no pagination token observed) —
      pluck/splat/browse don't special-case page count, so a
      multi-page account needs no further code, only a capture to
      verify against.

## Remaining rungs (mirror the claude ladder)

- [x] `chatfs_aistudio_conversation_render.py` — landed 2026-07-11.
      Confirmed linear/fork-less first (see
      `dev.kb/claims.kb/aistudio-jspb-prompt-shape.md`'s "Turn order is
      linear" section): the 15-turn demo capture is a flat, strictly
      increasing-`createTime` list with no parent/child field anywhere
      in the wire shape, so `build_tree` is a straight predecessor
      chain reusing `chatfs_render.render_tree` — the fork machinery
      (replies/superseded-by/backlinks) degenerates to a no-op on every
      node, verified against the live-rendered `chat.md` (no `re:`,
      `replies:`, or `superseded` strings anywhere in the 15-turn
      output). `chatfs_aistudio_conversation_render_test.py` covers
      stem parsing, turn loading (including the epoch→local-wall-clock
      conversion and the bodiless-turn skip), tree chaining, and the
      plain-sequence render; two hand mutations (dropped `.thought`
      note, broken chain parent) each turned exactly one test red,
      reverted clean.
- [x] `chatfs_aistudio_conversation_path_render.py` — landed 2026-07-11,
      byte-for-byte the claude shape (purge non-`.data` contents → splat
      → move `messages/` up → render `chat.md`). `url_browse.py` now
      delegates to it (was: stopped after `place_meta`, splat run by
      hand). Live-tested end-to-end against the demo capture.
- [x] `chatfs_aistudio_conversation_path_browse.py` / `..._url_render.py` —
      done 2026-07-11 (Immediate plan step 4), byte-for-byte the
      claude/chatgpt shape, built against the newly-shared
      `chatfs_layout.capture()` rather than written a third time from
      scratch. `path_browse` required adding
      `chatfs_aistudio_types.is_index_item` (claude/chatgpt already had
      one; aistudio didn't yet). Verified end-to-end with a stubbed
      `har-browse` replaying a real captured CDP stream, in an isolated
      scratch chat dir: capture → massage → splat → render produced the
      same 15-turn, 439-line `chat.md` as the existing demo fixture.
- [x] ~~Tech debt: splat still reads raw positional JSPB~~ **Upgraded to
      bug** (2026-07-03 review) and **fixed** (2026-07-03): splat and
      `layout.index_item` now read `conversation.json`'s named projection
      (`prompt.chunkedPrompt.chunks[]` / `prompt.metadata`) instead of
      positionally indexing raw JSPB — see devlog
      `../../devlog/2026-07-11-002-unification-shared-capture-and-drift-fixes.md`
      for verification (the driving todo.kb file, cross-provider-data-flow-drift,
      is deleted now that it's fully executed). The `create_time`-is-really-
      `lastModified` mislabel, tracked as a separate item in that same file,
      is also **fixed**
      (2026-07-04): `index_item` now anchors on the first chunk's
      `createTime` (true creation), not `lastModified.revisionTime`
      (modification).
- [ ] Latent fragility in `turn_kind()` (`chatfs_aistudio_conversation_splat.py`):
      `TURN_IS_ANSWER` (slot 16) is really `finishReason` (per rosetta's
      ground-truth-verified schema — see
      `dev.kb/claims.kb/aistudio-jspb-prompt-shape.md`'s 2026-07-03
      cross-check), and `== 1` is a proxy that happens to hold in every
      capture seen so far. A future capture with a non-`1` finish reason
      (`MAX_TOKENS`, `SAFETY`, error) would fall through `turn_kind`'s
      `raise`. Not yet observed — harden if/when it is.

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
- AI Studio is a third *browser-captured* provider. This strengthened
  the shared-lib signal earlier than the claude-code trigger originally
  assumed (in the now-deleted `todo.kb/2026-05-11-001-shared-code-among-providers.md`) —
  already revisited in `design.kb/040-design.kb/provider-plugin-model.md`
  § "Revised rule-of-three take".
