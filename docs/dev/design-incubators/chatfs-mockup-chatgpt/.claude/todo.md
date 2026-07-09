---
managed-by: Skill(llm-subtask)
cost-benefit-sweh:
  timebox:
    "@value": 3.0
    rationale: >
      Residual after chatgpt fork-fact parity landed via shared
      chatfs_render.py (2026-07-06, devlog). Unchecked items: match/case
      exhaustiveness sweep for chatgpt + both `*_render.py` (~1h),
      har-browse has_more=false wait fix (~2h), branch enumeration in
      claude splat (~1h), provider-plugin-model.md promotion (~0.5h),
      debug-intermediates flag (~0.5h). Strategic items (claude-code
      provider, shared code, rename, AI Studio ladder, cross-provider
      drift) tracked as child `.kb` refs with their own estimates.
    confidence: tentative
  benefit-2w:
    "@value": 1.0
    rationale: >
      All three providers (chatgpt, claude, AI Studio) are now MVP-complete
      and pyright-clean; remaining items are polish (branch enumeration)
      or infra hygiene (har-browse wait, debug flag), not blocking
      further provider work.
    confidence: tentative
  cost-of-delay-2w:
    "@value": 0.2
    rationale: >
      No external deadline; low urgency now that all three providers
      round-trip cleanly and typecheck clean. (The "too-many-changes"
      freeze was drained 2026-05-19 — archive/too-many-changes; worktree
      removed.)
    confidence: tentative
---

# Tactical Tasks — chatfs-mockup-chatgpt

Scope: this incubator only. Project-wide tactical work lives in
`../../../../.claude/todo.md`.

Completed work through 2026-07-05 (claude MVP + entry points + content-type
rendering, the shared `chatfs_layout.py` refactor, the URL-driven-capture +
noun-verb rename, the pyright-clean sweep) is recorded in `../../../devlog/`
— see 2026-04-29-000, 2026-05-11-001, 2026-05-12-000, 2026-07-05-000, and
2026-07-05-001.

## Next

- [ ] Add chatgpt-specific tests for `normalize_turnless`'s synthetic-anchor
      path (a turn-less fork materializing a heading) against a real
      `mapping` shape — found while closing the `before`..HEAD code-half
      review (2026-07-08): the 2-conversation demo corpus never triggers it,
      so it's covered only by the generic `chatfs_render_test.py` fixtures,
      never by chatgpt's actual wire shape. `primary_child`'s tie-break is
      similarly unverified against chatgpt's `create_time` (vs. the
      second-resolution claude case it was written for).
- [ ] [Cross-provider data-flow drift — pre-unification fixes vs unification scope](todo.kb/2026-07-03-000-cross-provider-data-flow-drift--pre-unification-fixes-vs-unification-scope.md)
      — from the 2026-07-03 three-provider review. All three "fix before
      unification" bugs landed 2026-07-03/04 (aistudio splat retarget,
      `create_time` mislabel, chatgpt failsoft→failfast) — the aistudio
      unification gate is clear. File stays open only for its "Solve by
      unification" section: five drift items recorded as requirements for
      the shared-code refactor, deliberately NOT fixed in place — see
      `~/.claude/sessions.kb/provider-code-reuse-stutter-step.md`
      (outside this repo; not a resolvable link).
- [ ] [Rename incubator to chatfs-cli-mockup](../../../../../.claude/todo.kb/2026-05-11-000-rename-incubator-to-chatfs-cli-mockup.md)
      — precursor to multi-provider sketch; current name encodes a single
      provider. Tracked at project level because the rename also touches
      `pyproject.toml` and the project ADR.
- [ ] Scan the rest of the incubator code for the implicit-match /
      `if X: return` … fall-through pattern and convert to explicit
      `match`/`case _:` (house exhaustive-case rule).
      `chatfs_claude_conversation_splat.py` already swept (2026-07-05, both
      the original session and the pyright-clean rewrite use `match`/`case`
      throughout); remaining: the `chatfs_chatgpt_*.py` siblings and both
      `*_render.py` (e.g. `render.py:primary_child`). Also recheck for
      fail-soft `.get()` guards and `ensure_ascii` while there.
- [ ] [AI Studio provider — parity ladder](todo.kb/2026-06-20-000-aistudio-provider-parity-ladder.md)
      — third provider, first JSPB source. Pluck + splat landed 2026-06-20;
      layout/types 2026-06-22; massage_json + url_browse 2026-07-03 (writes
      conversation.raw.json + conversation.json + meta.json end-to-end,
      live-tested). Index rung, render/path_render, and browse automation
      remain — url_browse doesn't yet delegate to a render step.

## Claude provider — remaining parity gaps

- [ ] Solve har-browse "wait until `has_more=false`". Observation: pressing
      "Done Capturing" shortly after the sidebar becomes interactable yields a
      CDP stream missing later index pages — cause underdetermined. Plan: a
      stop-when filter downstream of pluck breaks on `has_more=false`;
      har-browse receives EPIPE and shuts down cleanly (per
      `packages/har-browse/.claude/todo.md` 2026-04-24-003).
- [ ] Branch enumeration in splat — emit `conversations/<branch>.md` symlinks
      per leaf
- [ ] Promote `provider-plugin-model.md` symlink to a real incubator entry, with
      two-provider lessons (what's truly provider-shaped, what's universal)

## Strategic

- [ ] [claude-code as next provider](todo.kb/2026-05-11-000-claude-code-as-next-provider.md)
      — after claude.ai parity; datasource `~/.claude/`, no BB1
- [ ] [shared code among providers](todo.kb/2026-05-11-001-shared-code-among-providers.md)
      — strategic placement of the parity-ladder Refactor entry

## Later

- [ ] Gate debug intermediates (e.g. `cdp.jsonl` tees) behind a flag, default
      off. Leaf scripts read stdin / write data to stdout / send progress to
      stderr; higher-level orchestrators take URL or ts-dir args and tee
      debug intermediates (e.g. `chatgpt.index.cdp.jsonl`, `<ts-dir>/cdp.jsonl`)
      unconditionally today.
