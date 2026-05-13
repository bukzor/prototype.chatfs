# Commits (Rust port)

Per-commit records for the rust-port work.

## What belongs here

One file per landed or in-progress commit, named `NNNN-slug.md`. See `../decisions.kb/documentation-conventions.md` for numbering (`0N00` initial, inserts via `0150`/`0825`/etc).

## What does NOT belong here

- Pre-planning future commits → charter TOC
- Long-lived contract specs → elsewhere in `dev.kb/` (commit doc references out)
- Cross-session hand-off notes → `../handoffs.kb/`

## Section contracts

- **`## Plan`** is for the doer. Approach, files touched, helpful hints. Loose. Removed or left as history at landing.
- **`## Outcomes`** is for the reviewer + resumer. Pre-defined acceptance criteria as checkboxes. Each criterion must be **observable** (testable / verifiable) — quality goals like "code is clean" belong in code review, not here. Ticked boxes = what shipped; unticked = what's pending.
- **`## Notes`** captures emergent findings (surprises during implementation). Distinct from Outcomes, which is for *intended* acceptance.

## See also

- `.template.md` — copy when creating a new commit doc
- `../procedures.kb/session-start.md` — after entering a session here
- `../procedures.kb/end-of-commit.md` — what to do when a commit lands
