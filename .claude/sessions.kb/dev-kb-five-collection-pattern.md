# Dev-kb organization: two patterns observed, one skill considered

Synthesized during the har-browse Rust-port meta-planning session
(2026-05-21). Working state, not a normative call.

## The two patterns

### Pattern A — current chatfs `dev.kb/`

Hosted at `packages/$pkg/dev.kb/` (and `docs/dev/*.kb/` for workspace-level
collections). Sub-collections organized by **topic + epistemic shape**:

- `$topic.kb/CLAUDE.md` — collection scope guide
- `$topic.kb/decision-*.md` — normative choices
- `$topic.kb/fact-*.md` — empirical findings
- `$topic.kb/gotcha-*.md` — surprising failure modes

Examples in tree:

- `packages/har-browse/dev.kb/ts-policy.kb/` — TS policy decisions / facts /
  gotchas
- `packages/har-browse/dev.kb/rust-port.kb/` — port-specific work-area
  (transient, deleted at cutover) with `decisions.kb/`, `facts.kb/`,
  `procedures.kb/`, `commits.kb/`, `handoffs.kb/`

Strengths:

- Co-locates content with the package or topic it concerns.
- Sub-collection structure (`decision-*` / `fact-*` / `gotcha-*`) is
  customizable per-topic.
- Transient sub-collections (work-areas like `rust-port.kb/`) have a
  natural place.

Weak spots noticed during this session:

- `decision-*` vs `fact-*` collapses two distinct epistemic shapes:
  observed-state-of-world ("Node 22 strips types by default") and
  point-in-time-verified-property ("the 27 flag entries match upstream SHA
  $X"). Future-agents re-verify these differently.
- "Decision" sometimes used for *generalizable rules* that future agents
  should apply broadly, not just within one fork. E.g.
  `rust-port.kb/decisions.kb/assertion-strategy.md` ("defer-and-runtime-
  assert") is closer to a principle than a one-shot decision — it
  prescribes a pattern for similar future situations.
- "Gotcha" is a useful flag but conflates "fact about surprising behavior"
  with "principle: watch out for X" — the first is observation-shaped,
  the second is principle-shaped.

### Pattern B — homedir-archeology `.claude/*.kb`

Observed at `~/claude/homedir-archeology/.claude/`. Five collections by
**epistemic role**, hosted under `.claude/`:

- `decision.kb/` — specific choice at a specific fork
- `principle.kb/` — generalizable "always do X" rule (one-off corrections
  promote here once a second instance triggers)
- `observation.kb/` — durable factual snapshot about state (incl.
  user-asserted facts)
- `verified-claim.kb/` — assertion backed by a re-runnable verification
  script
- `reference.kb/` — stable external pointer (URLs, paths, canonical specs)

Plus `sessions.kb/` for narrative records of working sessions that haven't
yet been distilled into the role-specific kbs.

Strengths:

- Epistemic-role classification gives natural homes — "where does this go?"
  collapses to "what kind of claim am I making?"
- Observation vs verified-claim split makes the epistemic gradient explicit;
  destructive actions can require verified-claim backing.
- Principle vs decision split immediately reclassifies "defer-and-runtime-
  assert" correctly.
- Reference.kb implements DRY for external pointers without making each
  citer recompute the canonical URL.

Weak spots / open questions:

- Pattern is in active evolution by the homedir-archeology user; treating
  it as fixed risks chasing a moving target.
- No per-topic grouping — `decision.kb/` mixes decisions about
  unrelated topics. Discovery within a busy `decision.kb/` may need
  conventions (filename prefixes, frontmatter tags) at scale.
- All collections live at one host directory (`.claude/`). Per-package
  scoping requires a host-dir-per-package convention; the homedir-
  archeology repo is a single project so it hasn't faced this.

## The case for `Skill(llm-dev-kb)`

A skill that codifies a hybrid:

- The five epistemic-role collections from Pattern B as the *primary*
  classification axis.
- Optional per-topic sub-collections (Pattern A's `$topic.kb/`) within or
  parallel to the role-keyed collections, when a topic has enough mass
  to warrant a dedicated mental scope.
- Multiple `.kb/` roots: one workspace-level (where? — see below), one
  per package or scope (likewise).

Candidate role for the skill:

- Define the five collections and their boundaries (replacing per-package
  re-derivation of "what belongs here").
- Provide host-directory discovery rules (where to look for `.kb/` roots
  from any cwd).
- Codify the lifecycle: when an observation graduates to a principle;
  when a principle is retracted; when a verified-claim staleness check
  re-runs.
- Possibly provide a `kb` CLI for listing, linking, promoting, pruning.

## Host-directory question (where do `.kb/` roots live?)

Three candidates surfaced during this session, none decided:

| Candidate | Pro | Con |
|---|---|---|
| `.claude/` (status quo per Pattern B) | Existing convention; matches homedir-archeology directly; one less directory to teach future agents about | Mixes development knowledge with harness/tooling config (`settings.local.json`, `worktrees/`) |
| `dev.kb/` per package | Cleanly namespaced "development knowledge"; matches current chatfs convention | Doesn't extend to workspace-level naturally (`<repo-root>/dev.kb/` is awkward against `docs/dev/`) |
| `docs/dev/{several}.kb/` | Lives under the existing `docs/` umbrella; matches what `docs/dev/technical-policy.kb/` already does | Conflates "documentation" (for humans) with "knowledge base" (for agents); not all .kb content is human-doc-shaped |

A skill could plausibly support any of these, with a discovery convention.
Current weak lean: `.claude/` for workspace-level (already in use here
as of this session), `docs/dev/{role}.kb/` for per-package — but this
split is itself a tradeoff between consistency and locality.

## Migration considerations (if Pattern B is adopted broadly)

Not prescriptive — flagging what would be in scope if we go this way:

- `packages/har-browse/dev.kb/ts-policy.kb/` → role-keyed:
  - `decision-strip-types-only.md` → `decision.kb/`
  - `decision-migration-substeps.md` → `decision.kb/`
  - `decision-tsconfig-enforcement.md` → `decision.kb/`
  - `fact-*` → split between `observation.kb/` (e.g. node-strip-types-
    default) and `verified-claim.kb/` (the ones backed by reproducible
    commands)
  - `gotcha-type-only-re-export.md` → likely `principle.kb/` (generalizes
    to "ambiguous re-exports under any type-erasing pipeline")
- `packages/har-browse/dev.kb/rust-port.kb/decisions.kb/assertion-
  strategy.md` → `principle.kb/defer-and-runtime-assert.md`
- `packages/har-browse/dev.kb/rust-port.kb/decisions.kb/port-to-rust.md`
  → `decision.kb/` (or workspace ADR — orthogonal axis)
- Per-topic mass: `rust-port` work-area might keep its current shape as
  a transient containing role-keyed sub-collections, or might dissolve
  into the top-level role collections with filename prefixes.

## Considerations for a skill author

Light on prescription:

- Don't lock in the host directory before two or three projects have
  tried it.
- Don't enforce a flat structure if topics naturally cluster — let the
  user introduce `$topic.kb/` containers under the role kbs when mass
  justifies them.
- Make the verified-claim verification script a *required* field, not
  optional. The whole epistemic-weight argument depends on it being
  re-runnable.
- Sessions.kb is the loosest collection; budget for pruning rituals
  (otherwise it becomes a transcript graveyard).
- Cross-link via stable IDs / filenames, not via "the doc with these
  three words in the title" — survives renames better.
- Frontmatter with `source:` (originating session or conversation) is a
  small habit with large long-term value (verified in homedir-archeology
  by the `policy-safe-automation-boundary.md` frontmatter).

## Not deciding here

- Whether to adopt Pattern B broadly across chatfs.
- Where the host directories live.
- Whether to actually build `Skill(llm-dev-kb)`.
- Migration timing for existing `dev.kb/` content.

This entry exists to make the comparison legible so the eventual decision
isn't made from scratch.
