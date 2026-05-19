# 2026-05-19: drain too-many-changes — execution

Follow-up to `2026-05-19-000-drain-plan-provenance-audit.md`. Executed the drain plan settled in that earlier session.

## Focus

Land the conservative slice of the freeze at `../prototype.chatfs.too-many-changes/` (snapshot `7ef4517`, branch `too-many-changes`) onto `main`; archive the branch with `archive/` prefix; remove the worktree.

## What Happened

**Phase 1 reread changed two material decisions.** The plan written yesterday made calls on Phase 3 content without reading the actual artifacts. Two reads in particular revised the call:

1. The "3 dev.kb discoveries" the plan wanted to skip turned out to be 3 *design.kb* documents — the FIFO completeness requirement spec, the three-source capture-loss taxonomy, and the drain-mechanism design rationale — not stray dev observations. Initially revised the plan to land them.

2. Then read the on-main `packages/har-browse/src/capture.mjs` and discovered the design.kb docs describe an API that didn't ship. Main's `harBrowseMark` binding dispatches only on `BARRIER:` payload prefix; Done detection still uses the DOM poll `document.getElementById("capture-done")?.dataset.clicked`. The closure devlog and design.kb describe the *forward-looking* pivot from that DOM poll to an in-band CDP marker (`harBrowseMark("DONE")`, `harBrowseMark()` no-arg drain handshake) — none of which landed. Reverted to "skip all Stream-2 paper trail" per the conservative posture.

**Two commits landed:**

- `8dc4c08 chatfs-mockup-chatgpt: capture() helper, recursive null-tolerant cross-check, jq tolerance for bodyless responses` — Stream 1 infra exactly as planned. `capture()` puts the har-browse + pluck round-trip in one place; captures now land directly in `.chat/$UUID/.data/` so failures leave bytes inspectable. Recursive `null_tolerant_mismatches` keeps the cross-endpoint cross-check from false-positive on superset schemas. Four `*_pluck.jq` filters tolerate bodyless `responseReceived` (the wire-format-permitted-handling principle in action).
- `00ec42d docs/dev: promote 4 learnings from chatfs-mockup-chatgpt to project scope` — `commits-bounded-by-test-assertion-change` and `linter-warnings-name-work-to-do` into a new `docs/dev/learnings.kb/`; `robustness-target-wire-format-permitted` and `zero-data-loss-is-the-correctness-target` into `docs/dev/technical-policy.kb/`. Only the robustness-target file needed editing — its in-doc "Promotion target" subsection was self-referential to the move now happening.

**One file from the freeze deliberately skipped: the incubator's `.claude/todo.md`.** The freeze had a ±4 diff there, but it was reverting the recent ownership-marker migration (`cd2ed85 Migrate ownership marker: anthropic-skill-ownership → managed-by`). Taking the freeze's version would un-migrate.

**Phase 4: branch renamed to `archive/too-many-changes` (4 commits: planning + snapshot + 2 plan-on-plan tweaks); worktree removed with `--force` because 5 uncommitted edits remained in the working tree (3 of them the same `anthropic-skill-ownership` reverts, 2 the BARRIER task-file in-progress edits). All discardable per the plan.**

## Decisions

- **Provenance-audit pattern paid off again.** Yesterday's session named the pattern "draft plans from `git diff --stat` without reading the actual artifacts produces plausible-sounding but wrong specifics." Today, Phase 1 reread caught two more instances of that pattern in the audited plan itself — the "3 dev.kb discoveries" framing was wrong (they're design.kb), and even after correcting that, the recommendation to land them was based on assuming they describe what landed (they don't). Each correction required reading the actual code on main, not just trusting the plan.
- **Conservative posture for paper trails works.** Two iterations of "what should we land?" converged on "less than the plan said, including less than my mid-flight revision said." When the freeze documents an unlanded design and there's no on-main work that needs them, the right move is leaving them in the archive branch rather than landing-and-editing.
- **Cross-worktree branch rename is straightforward.** `git branch -m too-many-changes archive/too-many-changes` worked from the main repo even though the branch was checked out in the freeze worktree — git auto-updates the other worktree's HEAD.

## Next Session

- After the drain commits landed, surfaced two abandoned side-worktrees (`chatfs-mockup-residuals`, `tail-latency-closure`) — both at `bd23dd1` with no commits ahead of main, only 3 modified `.claude/todo.kb/*` files each (reverts of the ownership-marker migration). At user instruction, removed both worktrees. The branch labels still exist pointing at `bd23dd1`; they preserve nothing unique and can be pruned with `git branch -D` whenever.
- Pending project-level todos in `.claude/todo.kb/` continue to wait: incubator rename, rust-port-kb home, polyglot package naming sweep, rust-port-kb scope refactor. None blocked.
- If a future BARRIER follow-up wants to land the DOM-poll → marker pivot or the drain handshake mechanism, the freeze's closure devlog (`2026-05-12-001-har-browse-tail-latency-closure.md`), three design.kb docs, and `runtime-bindingcalled-fifo-with-network-rwb.md` claim are recoverable via `git checkout archive/too-many-changes -- <path>`. They're a coherent starting point, just describing a design state that wasn't reached on main.

## See Also

- Plan + audit record: `.claude/todo.kb/2026-05-19-000-drain-too-many-changes-freeze.md` (the "Closeout" and "Revisions" sections are the auditable narrative of decisions made during execution).
- Yesterday's calibration session: `docs/dev/devlog/2026-05-19-000-drain-plan-provenance-audit.md`.
