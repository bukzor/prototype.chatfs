---
managed-by: Skill(llm-subtask)
cost-benefit-sweh:
  timebox:
    "@value": 3.5
    rationale: >
      Updated 2026-07-12: match/case sweep and provider-plugin-model.md
      promotion (previously counted here) landed 2026-07-09; the Immediate
      plan (rename, AI Studio index/render/unification) closed 2026-07-11.
      Remaining unchecked items: har-browse has_more=false wait fix (~2h,
      cause still underdetermined), branch enumeration in claude splat
      (~1h), debug-intermediates flag (~0.5h). AI Studio's turn_kind()
      hardening and the reasoning-turn-mapping design question are
      deliberately unscheduled (deferred until/if a triggering capture is
      observed), not counted here. Strategic items (claude-code provider)
      tracked as a child `.kb` ref with its own estimate.
    confidence: tentative
  benefit-2w:
    "@value": 1.0
    rationale: >
      All three providers (chatgpt, claude, AI Studio) are now feature-complete
      (render/path_render/entry points/unification all landed) and
      pyright-clean; remaining items are polish (branch enumeration) or infra
      hygiene (har-browse wait, debug flag), not blocking further provider work.
    confidence: tentative
  cost-of-delay-2w:
    "@value": 0.2
    rationale: >
      No external deadline; low urgency now that all three providers round-trip
      cleanly and typecheck clean. (The "too-many-changes" freeze was drained
      2026-05-19 — archive/too-many-changes; worktree removed.)
    confidence: tentative
---

# Tactical Tasks — chatfs-cli-mockup

Scope: this incubator only. Project-wide tactical work lives in
`../../../../.claude/todo.md`.

Completed work through 2026-07-05 (claude MVP + entry points + content-type
rendering, the shared `chatfs_layout.py` refactor, the URL-driven-capture +
noun-verb rename, the pyright-clean sweep) is recorded in `../../../devlog/` —
see 2026-04-29-000, 2026-05-11-001, 2026-05-12-000, 2026-07-05-000, and
2026-07-05-001.

## Immediate plan (agreed 2026-07-10)

Sequence agreed with user; details live in the items/files referenced.

- [x] 1. **Finish the rename to `chatfs-cli-mockup`** — done 2026-07-10:
      `git mv` + repo-wide reference sweep, README closing rewrite
      (graduation target `$REPO/lib/chatfs/`, not `packages/chatfs-cli/`),
      done-notes in project todo, pyright + pytest clean, one rename-only
      commit ("Rename incubator chatfs-mockup-chatgpt -> chatfs-cli-mockup";
      the concurrent focus.md removal committed separately, "Remove dead
      .claude/focus.md convention"). Full verification in
      `../../../../../.claude/todo.kb/2026-05-11-000-rename-incubator-to-chatfs-cli-mockup.md`.
- [x] 2. **Live-capture sitting — AI Studio index** (needs user at an
      authenticated browser): reverse-engineer the index endpoint (likely
      `ListPrompts`), then write the index rung at the same sitting —
      `chatfs_aistudio_index_pluck.jq` + `chatfs_aistudio_index_splat.py`
      + `..._index_browse.sh` (the layout half landed 2026-06-22).
      Done 2026-07-11 (devlog): endpoint confirmed as `ListPrompts`
      (fires from `/library` and any `/prompts/<id>` page alike), shares
      `ResolveDriveResource`'s PROMPT/METADATA schema verified via
      `aistudio-schema/rosetta/` (pivoted to this RPC). Surfaced and
      fixed a real bug this unblocked: `chatfs_aistudio_layout.py::
      index_item()`/`IndexItem` assumed `create_time` from
      `chunkedPrompt.chunks[0]`, unavailable on index entries — now
      `NotRequired`, with an honest always-present `last_modified`
      alongside it (no-partial-synthesis.md), and the view tree labels
      every date-based placement (`Created=`/`LastModified=`,
      `chat-as-directory.md`). `_pluck.jq`/`_splat.py`/`_index_browse.sh`
      written and live-tested against this account's 42 prompts — no
      pagination token observed (account's prompt count fits one
      `ListPrompts` page).
- [x] 3. **Finish AI Studio's conversation side** — done 2026-07-11:
      `chatfs_aistudio_conversation_render.py` (verified the
      linear/no-forks assumption first — see
      `dev.kb/claims.kb/aistudio-jspb-prompt-shape.md`'s "Turn order is
      linear" section — then reused `chatfs_render.render_tree` over a
      degenerate straight-chain tree), `chatfs_aistudio_conversation_path_render.py`
      (byte-for-byte the claude shape), and `url_browse` now delegates
      to it (was: stopped after `place_meta`, splat run by hand). Live
      end-to-end tested against the demo capture (15 turns, no fork
      artifacts in the output); new
      `chatfs_aistudio_conversation_render_test.py` (9 tests,
      mutation-checked). Deliberately did NOT write
      `path_browse`/`url_render`: those fold into step 4. `basedpyright .`
      0/0/0; `pytest .` 28/28 pass (was 19).
- [x] 4. **Unify** — done 2026-07-11: executed
      [cross-provider drift](todo.kb/2026-07-03-000-cross-provider-data-flow-drift--pre-unification-fixes-vs-unification-scope.md)
      § "Solve by unification", all five requirements (see that file for
      per-item verification). `chatfs_layout.py` gained shared
      `capture(url, chat_dir, pluck_script, *, conversation_filename=...)`
      and `run_pluck(script, src, dst)`; every provider's `capture()` is
      now a thin wrapper over the shared one, and chatgpt's url_browse
      dropped its tempdir+move idiom for claude's direct-to-`.data/`
      policy. New shared `chatfs_url_browse.py` holds
      `null_tolerant_mismatches`, now exercised by chatgpt too (with a
      `_index_shaped()` normalization step chatgpt needs that claude
      doesn't — see the drift file). `packages/bukzor.chatgpt-export`'s
      splat now wraps reasoning/tool content in
      `<details type="thinking"|"tool_call">` like claude/aistudio
      (TDD, 4 new tests, verified live against a real 262-message
      capture). New `chatfs_aistudio_conversation_path_browse.py` +
      `..._url_render.py` close AI Studio's entry-point gap, built
      against the shared `capture()` (required adding
      `chatfs_aistudio_types.is_index_item`, mirroring
      claude/chatgpt). Driver-model decision documented in new
      `design.kb/040-design.kb/driver-model.md` (sibling to
      `cli-command-shape.md`, not nested inside it — see that doc for
      why), naming today's `capture()`/`run_pluck()` unification as its
      first landed instance and flagging splat/render's still-
      subprocess-composed orchestration as an explicit follow-on, not
      required to close this item. `basedpyright` 0/0/0 (incubator);
      `pytest` 76/76 pass (incubator 28 + chatgpt-export 48, was 28 + 44).
      Lib destination (`$REPO/lib/chatfs/` once libraryized) is a
      separate, later promotion step, not part of this unification.

Not scheduled here, still open: branch enumeration, the
debug-intermediates flag, the `last-updated` schema fix (all below), and
claude-code-as-provider (needs its design discussion first).

## Next

- [x] `chatfs_layout.py::time_dir_for`/`place_meta` have zero direct test
      coverage (checked 2026-07-11: no `*layout_test.py`, no grep hits
      for either name in any `*_test.py`) — pre-existing gap, but the
      2026-07-11 `label=`/"graduation" behavior (aistudio's
      `Created=`/`LastModified=` switch, purge-and-replace when a
      `LastModified=`-placed entry later gets real `create_time`) landed
      with none either. Worth a focused test: `time_dir_for` with/without
      `label`, and `place_meta` called twice for the same id/root with
      different labels asserting the first symlink is gone and the
      second is in its place. Done 2026-07-12: new `chatfs_layout_test.py`
      (4 tests, TZ pinned to `America/Chicago` via the same
      `monkeypatch`+`time.tzset()` pattern the aistudio render test uses),
      covering both cases named above. Mutation-checked by hand: dropping
      the `label=` prefix in `time_dir_for` turned all 4 tests red;
      disabling `_purge_view_symlinks` in `place_meta` turned exactly the
      relabel test red; both reverted clean. `basedpyright .` 0/0/0;
      `pytest .` 32/32 pass (was 28).

- [x] Add chatgpt-specific tests for `normalize_turnless`'s synthetic-anchor
      path (a turn-less fork materializing a heading) against a real `mapping`
      shape — found while closing the `before`..HEAD code-half review
      (2026-07-08): the 2-conversation demo corpus never triggers it, so it's
      covered only by the generic `chatfs_render_test.py` fixtures, never by
      chatgpt's actual wire shape. `primary_child`'s tie-break is similarly
      unverified against chatgpt's `create_time` (vs. the second-resolution
      claude case it was written for). Done 2026-07-09: extracted
      `make_turn`/`render_conversation` out of `main()` (they were an untestable
      closure/inline body — same pure-pipeline shape claude's renderer already
      has) into new `chatfs_chatgpt_conversation_render_test.py`, covering both
      gaps with chatgpt-shaped fixtures (`mapping`/`message.create_time` float,
      stem-derived synthetic anchor). Mutation-checked: flipping the tie-break
      direction and swapping the synthetic anchor's `.json` link for `.md` each
      turned exactly the new tests red; reverted clean. `basedpyright .` 0/0/0;
      `pytest .` 19/19 pass (was 15).
- [x] [Cross-provider data-flow drift — pre-unification fixes vs unification scope](todo.kb/2026-07-03-000-cross-provider-data-flow-drift--pre-unification-fixes-vs-unification-scope.md)
      — done 2026-07-11: every item in both the "Fix before unification" and
      "Solve by unification" sections, plus Success Criteria, is now `[x]`
      (Immediate plan step 4 executed the latter). File can be archived/
      deleted at a future session-end; left in place for now as the
      verification record.
- [x] [Rename incubator to chatfs-cli-mockup](../../../../../.claude/todo.kb/2026-05-11-000-rename-incubator-to-chatfs-cli-mockup.md)
      — done 2026-07-10 (Immediate plan step 1, above); this bullet was a
      stale duplicate left unchecked. That file's own Success Criteria are
      all `[x]`, verified 2026-07-10.
- [x] Scan the rest of the incubator code for the implicit-match /
      `if X: return` … fall-through pattern and convert to explicit
      `match`/`case _:` (house exhaustive-case rule). Done 2026-07-09: swept
      `chatfs_chatgpt_*.py` + both `*_render.py` — only three genuine violations
      found (none are enum/variant dispatch, so each became explicit
      `if`/`elif`/`else` rather than `match`/`case`):
      `chatfs_render.py::primary_child`, `chatfs_render.py::divider`,
      `chatfs_chatgpt_layout.py::_created`. Checked `.get()` call sites (all
      legitimate `NotRequired` TypedDict access, already assert-guarded) and
      `ensure_ascii` (consistently `False` everywhere it appears; chatgpt's
      splat lives outside this incubator, in `packages/bukzor.chatgpt-export/`,
      out of scope here) — no changes needed. Verified: `basedpyright .` 0/0/0;
      `pytest .` 15/15 pass.
- [ ] [AI Studio provider — parity ladder](todo.kb/2026-06-20-000-aistudio-provider-parity-ladder.md)
      — third provider, first JSPB source. Pluck + splat landed 2026-06-20;
      layout/types 2026-06-22; massage_json + url_browse 2026-07-03 (writes
      conversation.raw.json + conversation.json + meta.json end-to-end,
      live-tested). 2026-07-11: index rung (pluck/splat/browse + the
      IndexItem honesty fix it surfaced), render + path_render, and
      path_browse + url_render (Immediate plan step 4, built against the
      shared `capture()`) all landed — every entry point now exists.
      Remaining: `turn_kind()`'s latent `finishReason == 1` fragility
      (harden if/when a non-1 value is observed) and the reasoning-turn-
      mapping design question.

## Claude provider — remaining parity gaps

- [ ] Solve har-browse "wait until `has_more=false`". Observation: pressing
      "Done Capturing" shortly after the sidebar becomes interactable yields a
      CDP stream missing later index pages — cause underdetermined. Plan: a
      stop-when filter downstream of pluck breaks on `has_more=false`;
      har-browse receives EPIPE and shuts down cleanly (per
      `packages/har-browse/.claude/todo.md` 2026-04-24-003).
- [ ] Branch enumeration in splat — emit `conversations/<branch>.md` symlinks
      per leaf
- [x] Promote `provider-plugin-model.md` symlink to a real incubator entry, with
      three-provider lessons (what's truly provider-shaped, what's universal;
      wording was stale from before aistudio landed as the third provider). Done
      2026-07-09: replaced the symlink to the parent project's abstract spec
      with a real entry recording the concrete three-way split verified against
      the landed code (identical-verbatim → `chatfs_layout.py`/
      `chatfs_render.py`; the 3-value `id`/`title`/`created` adapter every
      `place_meta` wrapper shares; what's genuinely provider-only) and a revised
      rule-of-three take (AI Studio's JSPB-vs-keyed split, not the claude-code
      trigger originally expected, turned out sufficient). `llm.kb-validate`
      clean.

## Strategic

- [ ] [claude-code as next provider](todo.kb/2026-05-11-000-claude-code-as-next-provider.md)
      — after claude.ai parity; datasource `~/.claude/`, no BB1
- [x] [shared code among providers](todo.kb/2026-05-11-001-shared-code-among-providers.md)
      — done 2026-07-11: the extraction landed 2026-07-05; boundary
      refinement answered by Immediate plan step 4 — `capture()`/
      `run_pluck()` joined `chatfs_layout.py`, but the endpoint
      cross-check (`null_tolerant_mismatches`) got its own
      `chatfs_url_browse.py` rather than also landing in `chatfs_layout.py`
      (storage/view-tree concerns vs. url-browse-orchestration concerns
      are different boundaries). Destination for eventual promotion out
      of the incubator remains `$REPO/lib/chatfs/` once libraryized (not
      `packages/chatfs-core/`) — that promotion itself is not scheduled.

## Later

- [ ] Gate debug intermediates (e.g. `cdp.jsonl` tees) behind a flag, default
      off. Leaf scripts read stdin / write data to stdout / send progress to
      stderr; higher-level orchestrators take URL or ts-dir args and tee debug
      intermediates (e.g. `chatgpt.index.cdp.jsonl`, `<ts-dir>/cdp.jsonl`)
      unconditionally today.
- [ ] `design.kb/040-design.kb/cli-command-shape.md`'s unquoted
      `last-updated: 2026-05-11` fails `llm.kb-validate` (schema wants a string;
      YAML parses the bare date as `datetime.date`). Found 2026-07-09 doing an
      unrelated gate check. Fix by either quoting the value here or adding the
      `format: date` datetime.date-passthrough accommodation to
      `040-design.jsonschema.yaml` (the sibling `claims.jsonschema.yaml` already
      documents that accommodation for its own date fields — copy its approach).
      Didn't fix inline: looks like it may overlap an active cross-repo schema
      migration in another session
      (`~/.claude/sessions.kb/penguin/schema-migrate-string-pattern-to-date.md`)
      — check there first so this doesn't collide with a broader fix.
      Checked 2026-07-10: KbValidator gained `type: date`/`instant`
      (llm-kb 5d64413) and the migration is underway — so the right fix
      is migrating `040-design.jsonschema.yaml`'s `last-updated` to
      `type: date` (the unquoted bare date becomes the valid form); do
      NOT quote the value.
