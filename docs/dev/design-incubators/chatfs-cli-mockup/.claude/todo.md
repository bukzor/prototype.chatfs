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
`../../../../.claude/todo.md`. Completed work is recorded in
`../../devlog/` (project-wide) and this incubator's own `devlog/` —
directory listing is the index, not restated here.

## Next

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
      CDP stream missing later index pages. **Two candidate root causes**
      identified 2026-07-22, both real bugs with fixes sketched (not yet
      implemented): the Done-click drain race
      (`packages/har-browse/.claude/todo.kb/2026-07-22-000-Done-Capturing-race-drops-in-flight-requests-with-no-drain.md`)
      and persisted-cache hydration
      (`packages/har-browse/.claude/todo.kb/2026-07-22-001-claude-ai-revisits-render-from-persisted-React-Query-IndexedDB-cache--so-capture-sees-no-conversation-traffic.md`).
      Which one owns *this* symptom is decidable now from existing captures:
      index-page URL with `requestWillBeSent` but no `responseReceived` →
      drain race; no `requestWillBeSent` at all → hydration (the
      discriminator step, first step, in the 000 todo). Close this bullet
      once the owning fix lands and this symptom is retested.
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
      intermediates (e.g. `chatfs.demo/chatgpt/.data/index.cdp.jsonl`,
      `<ts-dir>/cdp.jsonl`)
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
