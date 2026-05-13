# Hand-offs (Rust port)

Inter-session hand-off notes — context that needs to cross a session boundary but doesn't fit in a commit doc.

## What belongs here

One file per topic. Filename `$topic.md` (snake_case). Self-contained: a future reader sees the filename in `ls` and may or may not read the body.

## When to add a file

- Mid-work discovery affecting an upcoming commit (e.g., "chromiumoxide 0.9.2 broke X, pin to 0.9.1")
- Specific resume instruction (e.g., "start by `cargo test -p playwright-lite`, expect panic in target_attach")
- Deferred decision needed before a specific commit (e.g., "decide JSONL `status` field shape before commit 1000")

## What does NOT belong here

- Permanent contracts (JSONL schema, BARRIER invariants) → elsewhere in `dev.kb/`
- Commit-scoped notes that fit in a commit doc → `../commits.kb/NNNN-slug.md`
- General development principles → `dev.kb/` root or `ts-policy.kb/`

## Format

Free-form prose. No required template. Keep it short — the action lives in the consumer's hands.

## Lifecycle

**Each hand-off is deleted when consumed.** See `../procedures.kb/consume-handoff.md` for the promote-vs-delete decision. Stale hand-off ≈ bug.
