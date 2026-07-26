# Devlog: 2026-07-26 — har-browse CLAUDE.md refresh and frontier session-entry retirement

## Focus

Repo-scope management, deliberately not implementation: make
`packages/har-browse` well-posed for a productive fresh `/session-start`.
Two gaps identified from a repo-root orientation pass: (1) har-browse's
`CLAUDE.md` was stale enough to actively mislead (described a
`captureEvents()` that no longer exists; pointed at a deleted `data/`
artifact; framed the package as a toy-only incubator), and (2) four
`sessions.kb` entries with `ended: null` matched the package's cwd, one
of them fully resolved but still presenting as an open thread.

## Decisions

### CLAUDE.md rewritten around current ground truth, not patched

**Rationale:** Nearly every section was stale (identity, key files,
design pointers), so a full rewrite against the verified tree was
cheaper and safer than incremental edits. New content: BB1-capture
framing, `attachCapture`/`startCapture` split, Done-button and BARRIER
protocol summaries (formal invariant pointer:
`tests/barrier_consumed.spec.mjs`), the puppeteer-core-migration
warning so new work doesn't deepen Playwright coupling, a Current Work
section (todo.md / todo.kb / ideas.kb / sessions.kb-by-cwd), and
`Skill(llm-subtask)` added to `depends:`.
**Alternatives considered:** Minimal patch of the Key Files list —
rejected; the header framing ("cleanroom subproject… local-only toy
app") was as misleading as the stale symbols.

### The paired `src/capture.mjs` BARRIER header comment was deferred

**Rationale:** A concurrent session is actively implementing the
cache-hydration fix (`clearOriginStorage`) in `capture.mjs`; this
session's header-comment edit was clobbered mid-flight by that
session's save (last-writer-wins). Rather than contend for the file,
the comment is carved out as its own todo.md bullet to land with the
hydration work, and CLAUDE.md's "mechanics:" pointer targets the
existing `inFlight`/`onBindingCalled` inline comments meanwhile.
**Alternatives considered:** Re-applying the edit — rejected: two
sessions racing on one file guarantees silent losses in one direction
or the other.

### `har-browse-capture-implementation-frontier` sessions.kb entry deleted

**Rationale:** Both of its live threads are absorbed into this repo:
the Playwright-demotion `[!QUESTION]` was ratified 2026-07-23 into
`packages/har-browse/.claude/todo.kb/2026-07-23-002-*` (and the
resolved `[!TODO]` in `design.kb/050-components.kb/toy-capture.md`),
and the comparison-table-vs-YAML shape decision is already a
har-browse `todo.md` bullet. The sessions.kb lifecycle is explicit:
entries whose follow-ups are absorbed elsewhere get deleted (git
history preserves them). Backlink grep before deletion found only
topic mentions (design.kb paths), no links to the entry file itself.
This leaves `har-browse-completeness-bugs` as the sole open capture
thread at that cwd; the two rust-port entries remain open because
their work is genuinely pending.
**Alternatives considered:** Setting `ended:` with a closing note —
rejected; the cwd-grep discovery recipe matches ended entries just the
same, so only deletion actually removes the false "open thread" signal.

### har-browse devlogs re-homed with the package (same session, later)

**Rationale:** har-browse had no `devlog/` of its own — its nine
session entries lived at repo-root `docs/dev/devlog/`, invisible to a
subpath `/session-start` (whose discovery find is cwd-relative).
Devlogs belong with the project they narrate (`Skill(llm-collab)`;
same ownership principle as todos), and the incubator and
aistudio-schema subprojects already keep their own. `git mv`'d all
nine har-browse-scoped entries to
`packages/har-browse/docs/dev/devlog/` (under the package's existing
`docs/dev/`, which is also where `llm-collab-devlog -C` targets),
added the skeleton `CLAUDE.md`, and left a breadcrumb in the root
devlog README. Reference sweep: sessions.kb devlog lists repointed to
the full repo-relative package path; moved-file sibling references
reduced to bare basenames.
**Alternatives considered:** package-root `devlog/` (incubator style)
— rejected for consistency with har-browse's existing `docs/dev/`
tree and the llm-collab skeleton.

Postscript to the deferred-header-comment decision above: the comment
landed later this same session at the user's direction, once the
hydration session's `capture.mjs` motion had settled; CLAUDE.md's
"mechanics:" pointer now targets it as originally intended.

## Conventions Established

- When a file is contested by a concurrent session, don't re-apply a
  clobbered edit — carve the change out as a todo for the session that
  owns the file's current motion.

## Open Questions

- None from this session. (The capture-hydration implementation was
  observed in flight, uncommitted, in `capture.mjs` /
  `tests/clear_origin_storage.spec.mjs` — its own session will account
  for it.)

## References

- `packages/har-browse/CLAUDE.md` — the rewrite
- `packages/har-browse/.claude/todo.md` — refresh bullet closed; header-comment bullet added
- `~/.claude/sessions.kb` commit `ec32208` — frontier entry deletion
- `2026-07-23-002-Frontier-ratification--doc-accuracy-pass--todo-restructuring.md` — the ratification this cleanup trails
