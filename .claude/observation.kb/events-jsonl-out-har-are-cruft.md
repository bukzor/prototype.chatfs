# `events.jsonl` and `out.har` at `packages/har-browse/` root are cruft

The files
- `packages/har-browse/events.jsonl`
- `packages/har-browse/out.har`

exist at the package root. Per user assertion (2026-05-21), these are
**interactive debugging cruft** from prior development sessions, not
load-bearing. They are not referenced by tests, scripts, or design docs.

## Disposition

- Move to `packages/har-browse/trash/` per the global trash convention
  (or workspace-root `trash/`).
- Or add to `.gitignore` and let them be regenerated locally on demand.

Either action is fine; the operative point is that no other work depends
on their presence at the package root.

Asserted by user 2026-05-21.
