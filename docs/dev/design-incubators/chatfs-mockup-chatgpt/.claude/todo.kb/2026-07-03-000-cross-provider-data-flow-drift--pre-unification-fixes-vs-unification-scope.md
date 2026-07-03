---
managed-by: Skill(llm-subtask)
cost-benefit-sweh:
  timebox:
    "@value": 4
    confidence: tentative
    rationale: |
      Pre-unification fixes ~2-3 SWEh (aistudio splat retarget +
      timestamp decision + failfast conversion). Unification-scope
      items cost nothing here — they're requirements recorded for the
      shared-code refactor already planned in
      2026-05-11-001-shared-code-among-providers.md.
  benefit-2w:
    "@value": 1.5
    confidence: tentative
    rationale: |
      Two live bugs (aistudio splat crashes on its documented input;
      date tree buckets aistudio by mtime) plus a silent-data-loss
      class on the chatgpt side. Fixing before unification prevents
      baking wrong semantics into the shared lib.
---

# Cross-provider data-flow drift — pre-unification fixes vs unification scope

**Priority:** Medium-high — two items are live bugs, and the split decides
what the unification inherits.
**Complexity:** Medium
**Context:** Full review in devlog
`2026-07-03-*` (this session); prior art:
[shared code among providers](2026-05-11-001-shared-code-among-providers.md),
[aistudio parity ladder](2026-06-20-000-aistudio-provider-parity-ladder.md).

## Problem Statement

A three-provider data-flow review (chatgpt / claude / aistudio) found the
primitives uniform (har-browse and the five plucks are consistent in
position and contract) but the orchestrators drifted. Some findings are
bugs to fix **before** unification (wrong semantics would otherwise be
baked into the shared lib, or block aistudio stabilization, which gates
unification). The rest are drift that unification should solve **by
construction** — fixing them in place first would be the same work twice.

## Fix before unification

Ordered: 1-3 stabilize aistudio (the unification gate); 4 is an
independent live bug on the chatgpt side.

- [x] **Retarget aistudio splat + `index_item` to the massaged doc.**
      `chatfs_aistudio_conversation_splat.py` crashed (`KeyError: 0`,
      verified) on its documented input: commit a5971ae made
      `conversation.json` the massaged named doc, but splat still
      positionally indexed raw JSPB (worked only on `conversation.raw.json`).
      Now reads `prompt.chunkedPrompt.chunks[]` by key (`role` / `isThought` /
      `finishReason` / `text`), mirroring how claude's splat reads
      `chat_messages`. Same move for `chatfs_aistudio_layout.index_item`
      (was reading raw `doc[0]` / `meta[4]` by index; now reads
      `prompt.name` / `prompt.metadata`) — `url_browse.py` updated to feed
      it the massaged doc instead of the raw one. After this, positional
      indices exist in exactly one place: `massage_json.py`'s SCHEMA.
      Supersedes the soft-worded "tech debt" rung in the parity ladder.
      Verified: splat's 15/15-turn `.md` output byte-identical to the
      pre-fix positional splat on the same capture; `index_item` returns
      the same id/title/create_time; pyright clean.
    - [ ] While there: basenames can carry per-turn timestamps — chunks
          have `createTime` (verified in the live capture). Docstring's
          false "JSPB has no per-turn id or timestamp" claim corrected;
          actually threading `createTime` into basenames deferred (not
          part of the crash fix). Note: user+thought turns can share a
          timestamp, so keep the index component for ordering.
- [ ] **Fix the `create_time` mislabel — decide the date-tree anchor.**
      JSPB meta slot 4 is `lastModified.revisionTime` (verified against
      rosetta's live `?alt=json` golden pair), but
      `chatfs_aistudio_layout.py:27` labels it `CREATED` and `meta.json`
      publishes it as `create_time`. Consequences: the aistudio date tree
      buckets by *modification* time where chatgpt/claude bucket by
      *creation* time, and re-capturing an active chat moves it to a new
      date-dir. Decide: anchor on honest `revision_time`, or derive
      creation from the first chunk's `createTime`. Then rename fields to
      match the decision.
    - [ ] Correct the same mislabel in
          `dev.kb/claims.kb/aistudio-jspb-prompt-shape.md`
          (`[0][4][4][0][0]` is revisionTime, not "created").
- [ ] **Convert chatgpt failsoft to failfast** (user-confirmed direction:
      "we want failfast"). Two sites where unknown content silently
      vanishes from `chat.md`:
    - [ ] `packages/bukzor.chatgpt-export/lib/bukzor/chatgpt_export/splat.py`
          `extract_text_content` — terminal `return None` on unknown
          `content_type` (line ~283). Should raise, like claude's
          `extract_text` does for unknown block types.
    - [ ] `chatfs_chatgpt_conversation_render.py:86-89` — silently skips
          nodes without an `.md`. Add claude-render's body-coverage
          assertion (`chatfs_claude_conversation_render.py:329`), with an
          explicit prune list for legitimately bodiless nodes.

## Solve by unification — do NOT fix in place

Requirements the shared-code refactor
(`2026-05-11-001-shared-code-among-providers.md`) must satisfy; recorded
here so they aren't re-discovered. Fixing any of these per-provider first
is wasted motion.

- [ ] **One shared `capture()`** (browse ⋅ pluck composition). Today: five
      copies, four idioms — claude's `layout.capture()` (direct-to-`.data/`,
      unlink-then-write), chatgpt url_browse (tempdir+move), chatgpt
      path_browse (direct+unlink, disagreeing with its own url_browse),
      aistudio url_browse (inlined claude idiom + massage). Adopt claude's
      documented policy: captures land in `.data/`, failures leave bytes
      inspectable. Note `capture()` is currently misfiled in a "layout"
      module — the shared-capture module wants to exist.
- [ ] **Persist every pluck output.** The conversation url_browse scripts
      (chatgpt, claude) run the index pluck a second time over the same CDP
      with `capture_output=True`; it's the only pluck whose output isn't
      tee'd to disk, contradicting the README's tee-intermediates policy.
      The shared orchestrator should tee it (e.g. `.data/index-pages.jsonl`).
- [ ] **Port claude's endpoint cross-check to all providers with two
      endpoints.** `null_tolerant_mismatches` (conversation doc vs index
      item) exists only on the claude side; chatgpt has the same two
      endpoints and no check. Belongs in the shared url_browse.
- [ ] **Make the `<details type=...>` grep contract provider-complete.**
      claude and aistudio splats wrap reasoning/tool content in
      `<details type="thinking|tool_call">`; chatgpt's splat writes them as
      bare markdown, so `grep 'type="thinking"'` silently misses chatgpt.
      The unified splat presentation layer fixes this once.
      (Related, already tracked in todo.md: bring chatgpt render to the
      fork-fact notation contract — same "claude is the reference
      implementation" shape.)
- [ ] **Decide the driver model: pipe vs delegation.** Index flow is
      user-composed (`index_browse.sh | index_splat.py`); conversation flow
      is nested delegation (url_browse → path_render → splat + render).
      Possibly intentional (bulk output has multiple consumers) but nowhere
      stated. Decide once, document in
      `design.kb/040-design.kb/cli-command-shape.kb/`, apply uniformly.

## Explicitly out of scope

- claude-render fork-facts back-port to chatgpt — already tracked in
  `todo.md` (claude ladder section) with the correct "after shared-lib
  refactor" sequencing.
- Index-splat duplicate-UUID handling difference (chatgpt asserts, claude
  tolerates) — provider-behavior-driven, called for.
- aistudio's missing rungs (index, render, orchestrators) — tracked in the
  [parity ladder](2026-06-20-000-aistudio-provider-parity-ladder.md).

## Success Criteria

- [ ] `chatfs_aistudio_conversation_splat.py conversation.json` runs clean
      on the massaged doc; `conversation.raw.json` has exactly one consumer
      (massage) and zero downstream readers.
- [ ] Positional JSPB indices appear in exactly one file
      (`chatfs_aistudio_conversation_massage_json.py`).
- [ ] `meta.json` field names are honest about which timestamp they carry;
      all three providers' date trees bucket by the same semantic.
- [ ] An unknown chatgpt content_type raises instead of vanishing.
- [ ] The unification requirements above are visible from the shared-code
      todo before its design starts.

## Notes

Review evidence (all verified by execution or direct read, 2026-07-03):
splat crash reproduced; `create_time`=revisionTime confirmed against
`docs/dev/aistudio-schema/rosetta/resolvedrive.alt-json.json` (the demo
date-dir `12:53:25-05:00` matches revisionTime, not first-chunk
createTime `12:42:40`); per-chunk `createTime` present in the massaged
demo doc.
