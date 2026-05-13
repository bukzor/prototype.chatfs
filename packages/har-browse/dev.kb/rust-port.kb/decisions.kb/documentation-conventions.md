# Decision: per-commit docs, emergent sessions

How this work is documented in `dev.kb/rust-port.kb/`.

## Conventions

- **Per-commit, not per-session.** Each completed/in-progress commit gets one short `commits.kb/NNNN-slug.md`. Sessions are emergent boundaries (where a quota or stopping point happened), not pre-planned scopes.
- **Commit numbering: `0N00`.** Four-digit, hundreds-spaced. Initial commits get `0100`, `0200`, ..., `1300`. Inserts use `0150`, `0825`, etc.
- **Commit doc has `## Outcomes`** as a checkbox list of observable acceptance criteria, written up-front and ticked as work progresses. All boxes ticked = commit ready to land. This is the most-cited part on resume — unticked boxes show what's still pending mid-commit, ticked boxes summarize what shipped post-commit. (Distinct from `## Notes`, which captures emergent surprises.) See `commits.kb/CLAUDE.md` for the template.
- **Hand-offs: many small files.** `handoffs.kb/$topic.md`, one topic per file. Created when needed, **deleted when consumed**. If a consumed hand-off represented durable knowledge, promote it to a contract doc before deletion. Stale hand-off ≈ bug.
- **Procedures** (session start, end-of-commit, hand-off consumption) live in `procedures.kb/`.
- **Commit-doc template** is embedded in `commits.kb/CLAUDE.md` — lives with its consumer.

## What lives where

| Content | Location | Lifespan |
|---|---|---|
| Charter | `dev.kb/rust-port.md` | Until commit 1300 |
| Facts informing the port | `rust-port.kb/facts.kb/` | Until commit 1300 |
| Decisions for the port | `rust-port.kb/decisions.kb/` | Until commit 1300 |
| Commit records | `rust-port.kb/commits.kb/` | Until commit 1300 |
| Open hand-offs | `rust-port.kb/handoffs.kb/` | Each, until consumed |
| Long-lived contracts (JSONL schema, BARRIER invariants, assertions) | `dev.kb/*.md` (elsewhere) | Survive the port |

## End-state sweep

At commit `1300`: `rm -rf dev.kb/rust-port.md dev.kb/rust-port.kb/`. Anything worth preserving must have been promoted out before. Sweep heuristic: *would you cite this in a future bug report or architecture conversation?*
