# Devlog: 2026-08-08 — design.kb reconciliation — graduation child 005

## Focus

Close the documentation half of the incubator's graduation (umbrella
child 005): move its design.kb to `packages/chatfs-cli/design.kb/`,
make the project 040 tower seams-only, record the graduation ADR, and
sweep dead links repo-wide. Three commits as planned, plus one
mid-sweep repair that grew a validator fix upstream.

## What landed

- **Commit A (`8385abb`)** — `git mv` of the incubator design.kb to
  `packages/chatfs-cli/design.kb/`, with every entry updated to ground
  truth *as it moved*: dotted module names post module-shape refactor,
  kebab entry points, required `--cache <dir>`, `.data/$UUID/meta.json`,
  the trash-skip clause in deterministic-regeneration. Ten backlink
  files updated (CLAUDE.md, HACKING.md, technical-policy, todos, ideas).
- **Commit B (`7b73518`)** — project `stack-split.md` rewritten
  seams-only (three runtimes, subprocess + files, one `[!TODO]` for the
  unbuilt Rust→Python invocation); full project-040 audit; the two
  residue items encoded as `[!QUESTION]` blocks in project
  `provider-plugin-model.md` (mount-root shape; whether a declarative
  manifest survives the adapter pattern). `[!TODO]` blocks added to
  sync-control-plane, work-enqueueing-model, user-interface — designed
  surfaces whose children (003/004) haven't landed.
- **Commit C** — graduation ADR
  (`docs/dev/adr/2026-08-08-000-chatfs-cli-graduates-from-the-incubator-with-its-design-kb.md`),
  incubator README pointer, this devlog, todo bookkeeping.
- **Sweep repair (`9324dba` + skills repo `3c7de8a`)** — the dead-link
  sweep's only hits were the five `docs/dev/aistudio-schema/discourse.kb/`
  schema symlinks, dangling since the skill renamed `schemas/` →
  `jsonschema/` (June 23). Replaced per user instruction with
  `$ref: skill://` stub files (llm-kb schema-reuse convention), placed
  as siblings of the collections — where the validator looks — not
  inside them where the symlinks had lived. First real `skill://` use
  exposed an llm-kb validator bug: an in-body `$schema` in a `$ref`
  target made jsonschema evolve() to that dialect's stock validator,
  dropping the custom `date`/`instant` types (UnknownType crash). Fixed
  upstream with a regression test. The first fix (`489562b`) stripped
  the declared `$schema` on retrieval; review overturned that as
  lie-tolerance. The landed fix (`3c7de8a`) instead gives the llmd
  dialect a declared, fetchable identity —
  `skill://llm-kb/jsonschema/dialect.jsonschema.yaml` — honored by
  validator selection on `$ref` crossings; unknown dialects and
  extension types under a stock dialect now error legibly instead of
  crashing or being guessed around. Restored validation surfaced 4
  frontmatter violations from the unvalidated six weeks — filed in
  `.claude/todo.md` Deferred, not fixed (schema-evolution territory).

## Decisions

### Docs follow the code; the project tower is seams-only

**Rationale:** `stack-split.md` drifted precisely because a project doc
asserted one package's internals — nothing that changed those internals
ever touched it. Scoping docs to the package whose changes invalidate
them removes the drift class, not just the instance.
**Alternatives considered:** fold entries into the project tower
(recreates the failure mode at scale); leave the kb in the closed
incubator (link rot); leave pointer stubs behind (interim convention is
backlink-sweep-on-move instead). See the ADR.

### Violations filed, not fixed

The 4 aistudio-schema frontmatter violations include `kind:
investigation` (×3), absent from the canonical sources enum — the right
fix may be an enum addition in llm-discourse-graph, which is exactly
the cross-kb conventions question 005's timebox says not to leak into.

## Conventions Established

- Moved design entries are corrected to ground truth in the same commit
  that moves them — a move is an audit, never a bare `git mv`.
- Schema reuse across repos is `$ref: skill://` stubs, not symlinks;
  the stub sits as the collection's *sibling* (`discourse.kb/x.jsonschema.yaml`
  beside `x.kb/`).

## Open Questions

- The two `[!QUESTION]` blocks in project `provider-plugin-model.md`
  (mount-root shape → settles with child 003; manifest-vs-adapters).

## References

- Plan: `.claude/todo.kb/2026-07-13-000-graduation-and-integration.kb/2026-07-13-005-design-kb-reconciliation-and-graduation-adr.md`
- ADR: `docs/dev/adr/2026-08-08-000-chatfs-cli-graduates-from-the-incubator-with-its-design-kb.md`
- Upstream fix: bukzor-agent-skills `3c7de8a` (supersedes `489562b`;
  `llm-kb/lib/python/llmd/`, `llm-kb/jsonschema/dialect.jsonschema.yaml`)
