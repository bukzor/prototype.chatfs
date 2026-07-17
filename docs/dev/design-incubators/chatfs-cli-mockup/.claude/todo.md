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
noun-verb rename, the pyright-clean sweep) is recorded in `../../devlog/` —
see 2026-04-29-000, 2026-05-11-001, 2026-05-12-000, 2026-07-05-000, and
2026-07-05-001. The Immediate plan agreed 2026-07-10 (rename to
`chatfs-cli-mockup`, AI Studio index rung, AI Studio conversation
render/path_render, and the four-provider unification) closed 2026-07-11 —
`../../devlog/2026-07-10-000-...` and this incubator's own
`devlog/2026-07-11-000-...`, `-001-...`, `-002-...`.

## Next

- [ ] [Atomic chat-dir regeneration — stage and rename, never rewrite in place](todo.kb/2026-07-13-000-Atomic-chat-dir-regeneration---stage-and-rename--never-rewrite-in-place.md)
      — first priority (user call, 2026-07-13 planning session): requirement
      `030-requirements.kb/atomic-cache-updates.md` is violated by in-place
      purge-and-rebuild; precondition for fuser-vfs integration.
  - [ ] [chatfs_locks: fill test stubs, migrate chatfs_atomic lock helpers, wire call sites](todo.kb/2026-07-17-000-chatfs-locks--fill-test-stubs--migrate-chatfs-atomic-lock-helpers--wire-call-sites.md)
        — the locking half: process-tree-reentrant lock table
        (`__CHATFS_LOCKS`) landed 2026-07-17 with 14/16 tests; remaining
        stubs + migration (migration blocked on coordinating with the
        active integration session).
- [ ] [AI Studio provider — parity ladder](todo.kb/2026-06-20-000-aistudio-provider-parity-ladder.md)
      — third provider, first JSPB source. Pluck + splat landed 2026-06-20;
      layout/types 2026-06-22; massage_json + url_browse 2026-07-03 (writes
      conversation.raw.json [renamed conversation.json.d/raw.json
      2026-07-15] + conversation.json + meta.json end-to-end,
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

## Strategic

- [ ] [claude-code as next provider](todo.kb/2026-05-11-000-claude-code-as-next-provider.md)
      — after claude.ai parity; datasource `~/.claude/`, no BB1

## Later

- [ ] Live-verify AI Studio's `conversation.json.d/raw.json` round-trip —
      run `chatfs_aistudio_conversation_url_browse.py` against a real
      prompt URL and confirm a correct `conversation.json` results. The
      2026-07-15 `.data/` scratch dot-d migration (devlog
      `devlog/2026-07-15-001-migrate-data-scratch-files-into-dot-d-sibling-directories.md`)
      was verified by test suite + basedpyright + a unit-level `pluck()`
      mkdir check only — no live Chromium/network access in that
      session's sandbox.
- [ ] [AI Studio: thread per-turn createTime into splat basenames](todo.kb/2026-07-12-000-AI-Studio--thread-per-turn-createTime-into-splat-basenames.md)
      — small, well-scoped; promoted 2026-07-12 from the deleted
      cross-provider-drift file's deferred scope. Closes the render-time
      timezone-dependency caveat noted in devlog `2026-07-11-001-...`.
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
