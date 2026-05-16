---
anthropic-skill-ownership: llm-subtask
status: exploring
cost-benefit-sweh:
  timebox:
    @value: "?"
    rationale: |
      Speculative; user mentioned "at some nebulous later date" during
      rust-port kb scope-refactor conversation (2026-05-15). Concrete
      timebox depends on what's getting migrated and Buck2's maturity
      at the time.
  benefit-2w:
    @value: 0
    rationale: |
      No 2-week payoff. Pure long-horizon refactor.
---

# Buck2 migration

## The Idea

Move the workspace's build orchestration onto Buck2 at some later date.

User mention (rust-port scope-refactor conversation, 2026-05-15, on Q4):

> Perhaps relevant (and perhaps not): I intend at some nebulous "later date"
> to move my stuff onto Buck2. That may offer prior art, inform design
> choices now. Possibly.

## Why it's an idea, not a todo

- No concrete trigger condition stated.
- No specific Buck2 milestone in the project plan.
- The user phrased it as "possibly relevant," not "I will do this."

## Open implications for current decisions (not blockers)

- **Polyglot package directory naming** (`rs-`/`py-`/`js-` prefix per Q4): Buck2's `BUCK` files declare toolchain per-target explicitly, so directory prefixes are not needed by Buck2 itself. Prefixes serve human/agent `ls` legibility, which Buck2 doesn't compete with. The two layers coexist; current convention is Buck2-neutral.
- **Cargo workspace layout** (`packages/<name>/Cargo.toml`): Buck2 supports Cargo via `buckle` / native Rust rules. Migration would replace Cargo with BUCK targets but preserve directory structure. Current layout is Buck2-portable.
- **Python (uv) and Node (pnpm) packages**: Buck2 has Python and JS rules. Same portability story.

Conclusion: nothing about Buck2 changes what we do now. Re-evaluate when (if) Buck2 migration becomes scheduled.

## Promotion criteria

Promote to a todo when ANY of:

- The user commits to a Buck2 migration timeline.
- Pain in the current multi-toolchain build coordination crosses a threshold (e.g., need for cross-toolchain target graphs, remote execution, etc.).
- A Buck2-relevant decision becomes blocked on this.

## Rejection criteria

Reject (delete this file) if:

- The user decides not to pursue Buck2.
- A different orchestrator (Bazel, Pants, etc.) becomes the chosen direction instead.

Either way: document the reasoning in an ADR before deletion.
