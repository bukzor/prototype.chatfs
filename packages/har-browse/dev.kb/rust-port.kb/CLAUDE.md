# Rust Port (transient work-area)

Active work-area for the Rust port of `har-browse`. See `../rust-port.md` for the charter.

## What belongs here

- Observable givens informing the port → `facts.kb/`
- Decisions made for the port → `decisions.kb/`
- Ritualized procedures (session start, end-of-commit, hand-off consumption) → `procedures.kb/`
- Per-commit records → `commits.kb/` (populated as work progresses)
- Inter-session hand-offs → `handoffs.kb/` (ephemeral)

## What does NOT belong here

- Long-lived contracts surviving the port (JSONL schema, BARRIER invariants, assertion implementations) → elsewhere in `dev.kb/`
- Package architecture rationale → `design.kb/`
- Tangential tactical todos → `.claude/todo.md` / `.claude/todo.kb/`

## Lifecycle

This directory is **deleted at commit 1300**. Before deletion, sweep for anything worth promoting to a permanent home in `dev.kb/`. Retention heuristic: *would you cite this in a future bug report or architecture conversation?* If yes, promote. If no, let it go with the sweep.
