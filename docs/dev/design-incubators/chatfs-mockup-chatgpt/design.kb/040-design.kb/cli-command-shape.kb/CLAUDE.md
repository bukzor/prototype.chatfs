# CLI Command Shape — Partition Rationale

Per-partition rationale for the noun-verb-locator CLI surface defined in
`../cli-command-shape.md`. Each entry captures durable rationale for a
partition prefix or instance where the content is substantive enough to
outgrow inline prose.

## What belongs

- **Per-noun summaries** (`noun=X.md`) when a noun carries paragraph-level
  rationale: what it is, lifecycle, why it matters.
- **Per-verb top-level docs** (`verb=Y.md`) when the verb-naming rationale
  is substantive on its own (e.g., parallel-section-level prose in the
  parent doc).
- **Sub-kb directories** (`noun=X.kb/`) when a noun has internal partition
  rationale (per-verb or per-locator within the noun) warranting its own
  files.

## What does NOT belong

- Per-script flow — lives in script docstrings.
- Naming conventions ($PATH kebab, Python underscores) — parent prose.
- Cross-noun verb-naming rationale below the substantive bar — parent prose.
- Storage layout — `../chat-as-directory.{md,kb/}`.
- Browse-incidental capture — `../browse-incidental-capture.md`.
- Regeneration semantics — `../deterministic-regeneration.md`.

## Partition-key convention

Entries use Hive-style `key=value` filenames. Reading a path reads a
partition: `noun=conversation.kb/verb=browse.md` is "the rationale at the
`conversation × browse` partition prefix."

## When to promote

Promote a per-prefix instance to its own file when its rationale exceeds
~50 tokens *and* spans more than one command at that prefix (e.g.,
`conversation × browse` spans both `url` and `path` locator forms).
