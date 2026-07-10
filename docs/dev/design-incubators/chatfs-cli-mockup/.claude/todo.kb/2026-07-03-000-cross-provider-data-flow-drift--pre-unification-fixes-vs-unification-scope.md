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
- [x] **Fix the `create_time` mislabel — decide the date-tree anchor.**
      Decided 2026-07-03: anchor on the first chunk's `createTime`
      (true creation), not `lastModified.revisionTime` (modification —
      verified live: revisionTime `12:53:25` trails chunk[0].createTime
      `12:42:40` by ~11 min on the demo capture). Matches chatgpt/claude's
      creation-time bucketing; neither provider's `IndexItem` carries a
      separate modified-time field, so no new field was added.
      `chatfs_aistudio_layout.index_item` now reads
      `chunkedPrompt.chunks[0].createTime`. Verified end-to-end: demo
      chat's view symlink moved from the `12:53:25` bucket to the
      `12:42:40` bucket; `meta.json` updated; pyright clean.
    - [x] Corrected the same mislabel in
          `dev.kb/claims.kb/aistudio-jspb-prompt-shape.md`
          (`[0][4][4][0][0]` is revisionTime, not "created"; added
          `previously-claimed:` entry and the turn-level `[32] createTime`
          field to the table).
- [x] **Convert chatgpt failsoft to failfast** (user-confirmed direction:
      "we want failfast").
    - [x] `packages/bukzor.chatgpt-export/lib/bukzor/chatgpt_export/splat.py`
          `extract_text_content` — terminal `return None` on unknown
          `content_type` now `raise ValueError(...)`, mirroring claude's
          `extract_text`. Verified: the 6 known content_types
          (text/thoughts/code/reasoning_recap/user_editable_context/
          model_editable_context) are the only ones present across every
          captured export in the repo (grepped); no unknown type has been
          observed yet, so this is latent-bug coverage, not a live fix.
    - [x] `chatfs_chatgpt_conversation_render.py:86-89` — investigated
          claude-render's body-coverage assertion
          (`chatfs_claude_conversation_render.py:329`) as a template, but
          its leaf-only prune-list design doesn't fit chatgpt's tree:
          verified against a live 188-message capture that 58 nodes are
          legitimately bodiless **non-leaf** pass-through nodes (blank
          system-context messages, empty thought summaries) — the common
          case here, not a rare edge case like claude's canceled-retry
          leaves. A leaf-only prune list produced 58 false-positive
          assertion failures on real data. Landed the narrower, correct
          invariant instead: `assert set(by_uuid) == set(mapping)`,
          guarding the stem-parsing directory scan against silently
          dropping a message id (the actual "vanishing" risk on the
          render side); the "unknown content_type" risk is fully covered
          by splat's raise above, at the source. Verified end-to-end:
          full pipeline re-run on the 188-message capture produced
          byte-identical `chat.md` output to pre-change; swept every
          demo chat with a captured `conversation.json` (2 of ~57 have
          one) — both clean, no assertion trips.

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
- [x] **Decide the driver model: pipe vs delegation.** Index flow is
      user-composed (`index_browse.sh | index_splat.py`); conversation flow
      is nested delegation (url_browse → path_render → splat + render).
      Possibly intentional (bulk output has multiple consumers) but nowhere
      stated. Decided 2026-07-10 (user): not either/or — each stage becomes
      an importable generator function, and the pipe and delegation
      surfaces are both thin drivers over the same library.
    - [ ] Document in `design.kb/040-design.kb/cli-command-shape.kb/` and
          apply during the unification refactor.

## Explicitly out of scope

- claude-render fork-facts back-port to chatgpt — already tracked in
  `todo.md` (claude ladder section) with the correct "after shared-lib
  refactor" sequencing.
- Index-splat duplicate-UUID handling difference (chatgpt asserts, claude
  tolerates) — provider-behavior-driven, called for.
- aistudio's missing rungs (index, render, orchestrators) — tracked in the
  [parity ladder](2026-06-20-000-aistudio-provider-parity-ladder.md).

## Success Criteria

- [x] `chatfs_aistudio_conversation_splat.py conversation.json` runs clean
      on the massaged doc; `conversation.raw.json` has exactly one consumer
      (massage) and zero downstream readers.
- [x] Positional JSPB indices appear in exactly one file
      (`chatfs_aistudio_conversation_massage_json.py`) — confirmed: no
      bracket-index reads remain in splat or layout.
- [x] `meta.json` field names are honest about which timestamp they carry;
      all three providers' date trees bucket by the same semantic
      (creation time).
- [x] An unknown chatgpt content_type raises instead of vanishing —
      `extract_text_content`'s terminal `else` now raises `ValueError`.
- [x] The unification requirements above are visible from the shared-code
      todo before its design starts — cross-linked from
      [shared code among providers](2026-05-11-001-shared-code-among-providers.md)
      Notes.

## Notes

Review evidence (all verified by execution or direct read, 2026-07-03):
splat crash reproduced; `create_time`=revisionTime confirmed against
`docs/dev/aistudio-schema/rosetta/resolvedrive.alt-json.json` (the demo
date-dir `12:53:25-05:00` matches revisionTime, not first-chunk
createTime `12:42:40`); per-chunk `createTime` present in the massaged
demo doc.
