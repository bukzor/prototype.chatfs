# Devlog: 2026-07-11 — rosetta/ pivots to ListPrompts golden pair

## Focus

Repoint `rosetta/`'s golden-pair capture/correlate/convert/verify loop from
`ResolveDriveResource` to `ListPrompts`, prompted by reverse-engineering work
on the sibling `chatfs-cli-mockup` incubator's AI Studio index rung (tracked
there, not here — see that incubator's own devlog for the index-rung side).

## Decisions

### `ListPrompts` entries reuse `ResolveDriveResource`'s PROMPT/METADATA JSPB schema — no new decode logic needed

Verified two ways: (1) manual positional cross-check against
`chatfs_aistudio_conversation_massage_json.py`'s existing `PROMPT`/`METADATA`
schema lined up slot-for-slot; (2) first-party confirmation via
`../curl-aistudio ListPrompts?alt=json`, which returns the real named
projection from the server itself. `rosetta/`'s convert→verify loop passes
clean reusing the *exact same* `SCHEMA` dict, zero changes. The only
difference: index entries have `chunkedPrompt: {}` (present, empty — no turn
content) instead of a populated `chunks[]`.

### `rosetta/` pivoted from `ResolveDriveResource` to `ListPrompts`

`rosetta/` (golden-pair capture/correlate/convert/verify loop) now targets
`ListPrompts` as its one live subject — `capture.sh`, `convert.py`'s
top-level unwrap (`{prompt: ...}` singular → `{prompts: [...]}` repeated),
`correlate.py`/`verify.py`/`check.do` fixture names all repointed to
`listprompts.{jspb,alt-json}.json`. The superseded `resolvedrive.*` golden
pair is `git rm`'d, not archived — the old pair is recoverable from git
history if `ResolveDriveResource`'s SCHEMA ever needs re-verifying
standalone. `redo check` passes.

## Conventions Established

- `rosetta/` holds one golden-pair subject at a time and is expected to be
  repointed (not extended) when the live investigative focus moves to a
  different RPC.

## Open Questions

- This "one pair at a time" convention is itself under review the same day
  it was written: holding N golden pairs concurrently (keyed by fixture
  filename, e.g. `resolvedrive.*` alongside `listprompts.*`) would let
  `verify.py` prove SCHEMA stability across structurally different subjects
  simultaneously, rather than resetting the evidence on each pivot — closer
  to actually resolving
  `../discourse.kb/questions.kb/can-we-decode-deterministically.md`'s open
  "exercise stability across prompt types" item. Not yet implemented.
- `ListPrompts` pagination shape (cursor/`has_more` field name and behavior)
  remains unobserved — this account's prompt count never triggered a second
  page against a 100-entry page-size request. Revisit if/when a larger
  account or a smaller requested page size is captured.

## References

- `../README.md` (rosetta/ section)
- `../rosetta/verify.py` output: `OK: listprompts.jspb.json converts
  similar-enough to listprompts.alt-json.json`
- `../discourse.kb/questions.kb/can-we-decode-deterministically.md`
