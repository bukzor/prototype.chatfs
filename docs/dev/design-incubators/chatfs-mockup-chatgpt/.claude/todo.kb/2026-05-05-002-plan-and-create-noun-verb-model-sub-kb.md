---
anthropic-skill-ownership: llm-subtask
status: done
---

# Plan and create noun-verb model sub-kb

**Priority:** Medium (will pay off as the CLI surface grows)
**Complexity:** Medium (planning + populating; design decision involved)
**Context:**
- `design.kb/040-design.kb/cli-command-shape.md` — current articulation
  of the noun-verb-locator model (single file, prose hierarchy + table)
- `Skill(llm-kb)` — promotion signals
- `Skill(llm-design-kb)` — design layers and `why:` chains

## Problem Statement

The noun-verb-locator naming scheme for pipeline scripts is articulated
in a single file (`cli-command-shape.md`) as a prose hierarchy and a
flat table mapping subcommand paths to script names. As the surface
grows (multi-provider, more verbs, more locator types), per-command
rationale and metadata accrue:

- Why each verb was chosen (`browse` over `capture`, `splat` as a verb
  of art, etc.).
- Per-noun lifecycle (which verbs apply, what locators are valid).
- Per-script status (implemented? planned? proven?).
- Cross-cutting properties (which scripts are leaves vs orchestrators,
  which are stdio vs target-addressed).

A flat table grows brittle. The user wants a sub-kb to track the model
concretely so that adding a new noun/verb has a clear home and the
relationships between commands stay legible.

## Current Situation

`cli-command-shape.md` contains:
- Prose hierarchy of provider/noun/verb/locator
- "splat as a verb" subsection (rationale)
- Script-names-on-PATH table (7 rows)
- Notes on internal-helper naming and module-name convention

The promotion signals are present (parallel-sections-of-same-type,
listing-heavy table, per-item growth pressure for verb rationale).

## Proposed Solution

Plan-out phase (this todo) before any kb creation:

1. Decide the per-file scope. Candidates:
   - **Per-noun.** `noun-index.md`, `noun-conversation.md`, future
     `noun-account.md`. Each lists its verbs/locators.
   - **Per-verb.** `verb-browse.md`, `verb-splat.md`, `verb-render.md`.
     Each notes which nouns it applies to, why-chosen.
   - **Per-command (noun×verb).** Most files; richest metadata; most
     entries. e.g. `index-browse.md`, `conversation-url-browse.md`.
   - **Hybrid.** Per-command for implemented scripts, per-noun/per-verb
     for narrative or design rationale.
2. Decide schema. Frontmatter candidates:
   - `noun:`, `verb:`, `locator:` (string or list)
   - `kind:` leaf | orchestrator
   - `address:` stdio | target | url
   - `status:` implemented | planned | rejected
   - `script:` filename
3. Decide whether `cli-command-shape.md` becomes
   `cli-command-shape.kb/` (with the file as summary) or whether the
   sub-kb is a sibling like `noun-verb-model.kb/`.
4. Survey current scripts to populate the kb at creation time.

Create phase (separate session):
1. Create the kb skeleton (CLAUDE.md, schema, summary file).
2. Populate one entry per chosen unit.
3. Cross-link to existing entries (`stdio-pipeline-shape.md`,
   `chat-as-directory.kb/pipeline-implications.md`).

## Implementation Steps

- [x] Pick per-file scope. Chose **partition-prefix**: a file exists
      when a partition prefix (`noun=X`, `verb=Y`, `noun=X × verb=Y`,
      `noun=X × locator=Z`) carries durable rationale spanning more
      than one command. Rejects all four planned candidates
      (per-command, per-noun, per-verb, hybrid) — none captured the
      "spans-multiple-commands" criterion that keeps the kb from
      growing brittle.
- [x] Design schema. Chose **prose-only, no frontmatter** on entries
      (summary file `cli-command-shape.md` carries `last-updated` per
      llm-kb).
- [x] Decide promotion strategy. Extended `cli-command-shape.md` into
      sibling `cli-command-shape.kb/` (llm-kb's `$CATEGORY.md` +
      `$CATEGORY.kb/` pairing).
- [x] Inventory current scripts + planned scripts for population.
- [x] Sketch CLAUDE.md content for the new kb.
- [x] Create the kb.
- [x] Update sibling docs (`stdio-pipeline-shape.md`,
      `chat-as-directory.kb/pipeline-implications.md`) — added a
      cross-link paragraph at the top of each, pointing at
      `cli-command-shape.md` + `cli-command-shape.kb/` for the
      noun-verb-locator framing.

## Open Questions

- Per-command vs per-noun: which scope minimizes redundancy while keeping
  files focused? Likely per-command, but per-noun gives a "what verbs
  does this noun support" glance.
- Should the kb include rejected/considered nouns and verbs as entries
  (with `status: rejected`)? Argument for: future sessions don't
  re-litigate. Argument against: ADR is the right home for that.
- Does the kb live under the chatgpt incubator (provider-scoped) or at
  project level (cross-provider)? Probably incubator now, with a
  promote-to-project step when claude.ai joins.

## Success Criteria

- [x] Plan-out decisions recorded (scope, schema, location). Recorded
      implicitly in `cli-command-shape.kb/CLAUDE.md` (what-belongs +
      partition-key convention + promotion rule).
- [x] User signs off on the plan before creation. Done interactively
      during the 2026-05-11 session.
- [x] kb created with entries for current scripts.
- [x] Sibling docs updated to point into the new kb.
- [x] Adding a new script (next session) requires only a new kb entry,
      not edits to multiple prose files.

## Notes

This is a planning todo, not an execution todo. Discussion with user
expected before any kb creation. The chat-as-directory factorization
took several rounds of structural discussion before final shape;
expect similar here.

## Resolution (2026-05-11)

Landed `design.kb/040-design.kb/cli-command-shape.kb/` with 10 entries
across two levels (top-level + `noun=conversation.kb/` sub-kb).
Partition-prefix scope, prose-only entries, Hive-style `key=value`
naming. Summary `cli-command-shape.md` gutted of listings (subcommand-
path block and script-name table both removed) and restructured into
partition-vocabulary glossary + explicit-locator policy + naming-
conventions rule. Open Questions resolved:

- **Per-command vs per-noun scope:** picked partition-prefix —
  promotes when rationale spans more than one command at a prefix
  AND exceeds ~50 tokens. Smaller and more growth-resistant than
  per-command would have been.
- **Rejected nouns/verbs as entries:** not included; ADR remains the
  right home for rejected designs.
- **Incubator vs project scope:** incubator (`chatfs-mockup-chatgpt/`)
  for now; promotion to project level deferred until claude.ai joins.

Devlog: `docs/dev/devlog/2026-05-11-000-chatfs-mockup-chatgpt-cli-command-shape-kb.md`.
