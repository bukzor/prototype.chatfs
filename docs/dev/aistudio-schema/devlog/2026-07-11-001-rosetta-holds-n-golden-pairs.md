# Devlog: 2026-07-11 — rosetta/ generalizes to N concurrent golden pairs

## Focus

Same-day follow-up to `2026-07-11-000-rosetta-pivot-to-listprompts.md`:
replace that entry's "one golden pair at a time" convention with holding
every known pair concurrently, so SCHEMA stability is proven across
structurally different subjects at once rather than reset on each pivot.

## Decisions

### The fixture filename is the subject key; the directory listing is the registry

No new config file: `<subject>.jspb.json`/`<subject>.alt-json.json` naming
(already the existing convention) doubles as the manifest of known golden
pairs. Any code path with a real path (`verify.py`, `correlate.py`) derives
`subject` from the filename stem. Only `convert.py`'s CLI lacks a filename
(it reads stdin, piped per the README idiom) — it alone takes an explicit
`SUBJECT` positional argument rather than guessing from JSON shape.

### `rosetta/` now holds both `resolvedrive` and `listprompts` golden pairs

Restored `resolvedrive.{jspb,alt-json}.json` from `19c5ea6~1` (the commit
that deleted them) alongside the current `listprompts.*` pair.

- `convert.py`: split `from_jspb` into `from_jspb_resolvedrive` /
  `from_jspb_listprompts` behind a `TOP_LEVEL` registry keyed by subject
  name. The two subjects differ only in top-level wrapper shape — singular
  `{prompt: ...}` vs. repeated `{prompts: [...]}` — the shared
  PROMPT/METADATA `SCHEMA` is unchanged, which is the evidence this whole
  exercise is after.
- `correlate.py`: analogous `REPRESENTATIVE` registry for per-subject
  representative-entry extraction (a singular prompt vs. one entry from a
  repeated page).
- `verify.py`: no-arg mode now globs `*.jspb.json`, pairs each with its
  `*.alt-json.json`, and checks all of them — exit 1 if any pair diverges.
- `check.do`: `redo-ifchange`'s glob picks up fixtures at build time, so a
  third subject needs no edit here.
- `capture.sh`: takes `SUBJECT` (`resolvedrive`|`listprompts`) as its first
  argument, dispatching to the right RPC/param.

**Result:** `./verify.py` reports OK for both subjects simultaneously;
`redo check` and `redo all` (pyright included) both pass.

**Alternatives considered:** sniffing the subject from JSPB shape instead of
filename/explicit-arg (rejected — fragile, and this package already treats
filenames as identity-bearing; explicit is cheap here since every call site
but one has a real path anyway).

## Conventions Established

- Supersedes `2026-07-11-000-...`'s "one pair at a time" convention:
  `rosetta/` now holds N golden pairs concurrently, one per RPC/message
  shape, keyed by fixture filename. A new subject is added by capturing its
  pair and registering it in `convert.py`'s `TOP_LEVEL` and `correlate.py`'s
  `REPRESENTATIVE` — never by replacing an existing pair.

## Open Questions

- `ListPrompts` pagination shape remains unobserved (carried over from the
  prior entry, unchanged by this session's work).
- Whether this fully resolves
  `../discourse.kb/questions.kb/can-we-decode-deterministically.md`'s
  "exercise stability across prompt types" item, or just advances it: two
  golden pairs now coexist and both pass against one shared SCHEMA, but
  neither specifically exercises a repeated field, a oneof, or a field
  present in one encoding and absent in the other — the scenarios the
  question names. A third pair chosen to hit one of those cases would be
  stronger evidence than a third pair chosen merely for breadth.

## References

- `2026-07-11-000-rosetta-pivot-to-listprompts.md` (superseded convention)
- `../README.md` (rosetta/ section, updated)
- `../rosetta/verify.py` output: OK for both `listprompts.*` and
  `resolvedrive.*`
- `../discourse.kb/questions.kb/can-we-decode-deterministically.md`
