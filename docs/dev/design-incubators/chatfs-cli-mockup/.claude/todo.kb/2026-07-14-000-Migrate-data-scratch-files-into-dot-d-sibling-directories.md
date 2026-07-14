---
managed-by: Skill(llm-subtask)
related-effort: docs/dev/technical-policy.kb/path-ownership.md
cost-benefit-sweh:
  timebox:
    "@value": 2.0
    rationale: >
      Mechanical rename across ~7 files (two call-site shapes, repeated
      per provider), plus a docstring and one design-doc touch-up. No
      design unknowns.
    confidence: tentative
  benefit-2w:
    "@value": 0.25
    rationale: >
      Internal cleanup only — closes a doc/code drift risk (the
      `[!TODO]` in path-ownership.md) rather than delivering
      user-visible value.
    confidence: tentative
---

# Migrate data scratch files into dot-d sibling directories

**Priority:** Low-Medium — orthogonal cleanup, blocks nothing downstream.
**Complexity:** Low
**Context:** Decided 2026-07-14 during path-ownership-contract-v1 work
(`docs/dev/technical-policy.kb/path-ownership.md`'s `.data/` section):
every top-level `.data/` contract name `X` (`meta.json`,
`conversation.json`, `cdp.jsonl`) reserves the sibling `X.d/` for
scratch related to producing or checking it — same shape as
`/etc/apt/sources.list.d/`. Path-ownership.md documents this as
`[!TODO] Not yet implemented`; this todo implements it.

## Problem Statement

Two ad hoc files sit at `.data/` top level today, distinguished from
the three contract names only by *not* matching one of them, not by
any structural marker:

- A pre-normalization pluck, written before a later step produces the
  canonical `conversation.json` from it.
- A cross-check dump, written while verifying the single-browse-trip
  optimization that also produces `cdp.jsonl`'s consumer.

Both should move under their respective `X.d/`.

## Current Situation

- Pre-normalization pluck: written to `.data/conversation.raw.json`,
  consumed by a massage step that writes `.data/conversation.json`.
  One provider's pipeline only. Call sites: its `layout.py` (`capture`
  wrapper), its massage script, its `conversation_url_browse.py` and
  `conversation_path_browse.py`.
- Cross-check dump: written to `.data/index-pages.jsonl` by url-browse's
  incidental-capture verification (`find_index_item`). Same shape at
  three call sites, one per provider's `conversation_url_browse.py`.
- `chatfs_layout.py`'s module docstring documents the old flat layout.
- One design doc
  (`design.kb/040-design.kb/cli-command-shape.kb/noun=conversation.kb/verb=browse.md`)
  names `conversation.raw.json` by its old top-level path.

## Proposed Solution

- Pre-normalization pluck moves to `.data/conversation.json.d/raw.json`
  (create the `.d/` dir before writing).
- Cross-check dump moves to `.data/cdp.jsonl.d/index-pages.jsonl`.
- No purge-logic changes needed: path render's purge allowlists `.data`
  wholesale and never looks inside it, so `.d/` subdirs are invisible
  to that step either way.

## Implementation Steps

- [ ] Update the four pre-normalization call sites to write/read
      `conversation.json.d/raw.json`, creating the dir as needed.
- [ ] Update the three cross-check call sites to write
      `cdp.jsonl.d/index-pages.jsonl`, creating the dir as needed.
- [ ] Update `chatfs_layout.py`'s module docstring and the
      `verb=browse.md` design doc to the new layout.
- [ ] Update `docs/dev/technical-policy.kb/path-ownership.md`'s
      `.data/` `[!TODO]` block: drop "Not yet implemented" once landed.
- [ ] Sweep `*_test.py` for the old paths after moving (none matched an
      initial grep, but re-check — tests may construct paths inline).

## Open Questions

- None — mechanical rename, same shape at every call site.

## Success Criteria

- [ ] No file under any `.data/` sits at top level except `meta.json`,
      `conversation.json`, `cdp.jsonl`; scratch lives under the
      matching `X.d/`.
- [ ] Full test suite + basedpyright clean; one live end-to-end capture
      on the provider that exercises the pre-normalization pluck still
      produces a correct `conversation.json`.

## Notes

Orthogonal to every child of the graduation-and-integration umbrella:
doesn't touch import structure (child 000), packaging/CLI surface
(child 001), the Rust side (children 003/004), or the atomic-regeneration
swap boundary (`.data/` is explicitly *input*, not the atomically-swapped
derived surface — see that todo's Proposed Solution). No `blocked-by`
edge either direction. Cheapest to land alongside child 000's
file-touching pass (same files, same motion) — noted there — but not
required to.
