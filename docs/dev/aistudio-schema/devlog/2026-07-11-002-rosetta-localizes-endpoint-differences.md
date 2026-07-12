# Devlog: 2026-07-11 — rosetta/ localizes endpoint differences to `endpoint/<name>/`

## Focus

Same-day follow-up to `2026-07-11-001-rosetta-holds-n-golden-pairs.md`: that
entry got two golden pairs coexisting, but the per-subject differences still
lived as central-registry entries (`convert.py`'s `TOP_LEVEL`, `correlate.py`'s
`REPRESENTATIVE`) keyed by a `subject` string threaded through every CLI, and
`rosetta/check` verified every pair in one combined redo target/process.
User-directed rework: move the differences into per-endpoint directories, and
give each endpoint its own independently-buildable redo target.

## Decisions

### Fixtures + endpoint config move to `endpoint/<name>/`; scripts take a directory, not a subject string

`resolvedrive.{jspb,alt-json}.json` / `listprompts.{jspb,alt-json}.json` at
`rosetta/`'s top level become `endpoint/resolvedrive/{jspb,alt-json}.json` /
`endpoint/listprompts/{jspb,alt-json}.json` — filenames drop the subject
prefix since the directory now carries identity. `convert.py`, `correlate.py`,
`verify.py`, and `capture.sh` all take an `ENDPOINT_DIR` argument in place of
the old `subject` string; none of them hard-code a subject list anymore.

### Per-endpoint differences are declared as *data* (`meta.json`), not code

The only things that vary per endpoint turn out to be expressible without
code: `method`, `default_param`, and a `{param}`-templated request `body`
(read by `capture.sh` via `jq`), plus `top_level_key`/`repeated` (the
singular-`{prompt: ...}` vs. repeated-`{prompts: [...]}` top-level wrapper,
read by `convert.py`/`correlate.py`). Each lives in
`endpoint/<name>/meta.json`. `convert.py` keeps the one shared PROMPT/METADATA
`SCHEMA` and gained a single generic `from_jspb(jspb, meta)`, replacing the
two hand-written `from_jspb_resolvedrive`/`from_jspb_listprompts` functions
and the `TOP_LEVEL` dict that dispatched between them. `correlate.py`
similarly gained one generic `representative(named, pos, meta)`, replacing
`REPRESENTATIVE` and its two per-subject functions.

**Alternatives considered:** per-endpoint Python modules (`endpoint.py` with
an importlib-loaded `from_jspb`/`representative`) — rejected once it became
clear the actual variation (wrapper key, singular/repeated, method name, param
encoding) has no branching logic in it, only values; a dynamic-import
mechanism would have added real complexity to express something `meta.json` +
one generic function already covers. Revisit if a future endpoint's
difference genuinely needs code (not just data) — nothing here forecloses
adding an optional per-endpoint code hook later.

### `verify.py`'s docstring correction: "shared SCHEMA" is a hypothesis under test, not a confirmed fact

While rewriting `convert.py`'s module docstring for the new N-endpoint-generic
phrasing, a first draft said the shared PROMPT/METADATA types were "confirmed
by structural alignment across their golden pairs." Caught in review: that's
circular — structural alignment across golden pairs is `verify.py`'s job,
every run, not a settled precondition `convert.py` gets to assert about its
own design. It also contradicted `../discourse.kb/questions.kb/
can-we-decode-deterministically.md`, which explicitly tracks this as **open**
(untested: a repeated field, a oneof, a field present in one encoding and
absent in the other). Reworded to state the one-shared-SCHEMA design as a
hypothesis that `verify.py` keeps testing per endpoint, and that a future
endpoint's divergence would be evidence against it, not a bug to patch around.

### Each `endpoint/<name>/` gets its own `check.do`; `rosetta/check.do` only aggregates

Previously `rosetta/check.do` ran `verify.py` once, checking every committed
pair in a single process/redo target — one endpoint's divergence didn't halt
reporting on the other (verify.py already checked all pairs before deciding
pass/fail), but the two were not independently *cacheable*: any fixture
change reran the whole combined check, and there was no per-endpoint target
redo could reason about independently. Now `endpoint/resolvedrive/check.do`
and `endpoint/listprompts/check.do` are real, independent redo targets (each
just `redo-ifchange`s its own `meta.json`/`jspb.json`/`alt-json.json` +
the shared `convert.py`/`verify.py`, then runs `verify.py .`). `rosetta/
check.do` depends on both via `redo-ifchange`, so redo tracks and can
parallelize them separately; touching only `listprompts`'s fixture rebuilds
only `endpoint/listprompts/check`, confirmed by `touch`-ing one fixture and
observing `redo check` skip the other.

**Gotcha:** `redo-ifchange endpoint/*/check` doesn't work as the aggregator body
— `check` targets don't exist as files until built, so an unmatched shell glob
under `sh` passes through *literally* instead of expanding (unlike our bash
tool's `failglob`, which would error instead — still wrong, just differently).
Fixed by globbing `endpoint/*/meta.json` (committed, always present) to
discover endpoint directories, then `redo-ifchange`-ing each one's `check`
by name in a loop.

## Conventions Established

- Per-endpoint differences live in `endpoint/<name>/` as data
  (`meta.json`) wherever they can be — code stays generic and shared,
  reserving a per-endpoint code hook for if/when a future endpoint's
  difference can't be expressed as data.
- Every `endpoint/<name>/` is an independent redo target
  (`endpoint/<name>/check.do`); aggregators (`rosetta/check.do`) discover
  member endpoints by globbing a committed file (`meta.json`), never by
  globbing the target they're building.

## Open Questions

- Carried over, unaffected by this reorganization: `ListPrompts` pagination
  shape remains unobserved; a third golden pair exercising a repeated field,
  a oneof, or a field present-in-one/absent-in-the-other would be stronger
  evidence for `can-we-decode-deterministically.md` than a third pair chosen
  merely for breadth.

## References

- `2026-07-11-001-rosetta-holds-n-golden-pairs.md` (superseded fixture-naming
  convention: `<subject>.{jspb,alt-json}.json` at `rosetta/` top level)
- `../README.md` (rosetta/ section, updated)
- `../discourse.kb/questions.kb/can-we-decode-deterministically.md`
