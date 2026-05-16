# Scope audit — `rust-port.kb/`

**Status:** Draft. Audit-as-deliverable per
`~/.claude/skills/llm-kb/docs/dev/case-studies.kb/2026-05-13-000-har-browse-rust-port-scope-refactor.md`.
No moves, no commits, no skeleton dirs from this pass. Review then execute.

## Method

Per the postmortem's procedure:

1. Read every content file in `packages/har-browse/dev.kb/rust-port.{md,kb}/` (32 files; done).
2. For each, identify the scope-homes its content spans — title scope ≠ content scope.
3. Surface splits (one file's content carved across multiple scope-homes).
4. Defer the original "where does the kb live" question until after content-splits are clear.
5. Note where future-package skeletons would need to exist.

Anti-patterns I'm avoiding: container-shuffling without opening files;
classifying by filename; refusing to address future packages because they don't
exist yet; iterating the wrong frame faster.

## Scope-home catalog

| Code | Path | Exists? | Lifespan | Purpose |
|---|---|---|---|---|
| **WS-bg** | `docs/dev/background.kb/` | yes | forever | Durable cross-cutting tech background (FUSE, HAR, Rust-Chrome, etc.) |
| **WS-pol** | `docs/dev/technical-policy.kb/` | yes | forever | Cross-cutting normative guidance |
| **WS-adr** | `docs/dev/adr/` | yes (1 entry) | forever | Workspace-level architectural decisions |
| **WS-dev** | `dev.kb/` (workspace root) | **no** | forever | Workspace-level dev practice |
| **PL-design** | `packages/playwright-lite/design.kb/` | **no** | forever | Crate-design rationale |
| **PL-adr** | `packages/playwright-lite/adr/` | **no** | forever | Per-crate ADRs |
| **PL-dev** | `packages/playwright-lite/dev.kb/` | **no** | forever | Per-crate dev gotchas |
| **HBR-design** | `packages/har-browse-rs/design.kb/` | **no** | forever | (parallel) |
| **HBR-adr** | `packages/har-browse-rs/adr/` | **no** | forever | (parallel) |
| **HBR-dev** | `packages/har-browse-rs/dev.kb/` | **no** | forever | (parallel) |
| **HB-dev** | `packages/har-browse/dev.kb/` | yes | until 1300 | Existing Node-side dev kb |
| **Trans** | `<TBD>/rust-port.kb/` | yes (current loc) | until 1300 | Transient port narrative |
| **Retire** | — | — | — | Delete with sweep; no preservation |

Future packages: per the postmortem, *empty skeletons are valid containers
now*. Each future crate gets the symmetric set: `CLAUDE.md`, `README.md`,
`design.kb/`, `dev.kb/`, `adr/`, `docs/technical-policy.kb/` (if needed),
`.claude/todo.kb/` (if needed).

The workspace-root `dev.kb/` also doesn't exist; create it if (and only if)
the audit produces workspace-wide dev-practice content.

## Per-file audit

Format: file → bullet per content section → scope(s) it belongs at. Multiple
scopes per file is the rule, not the exception.

### `rust-port.md` (charter)

- **Why / pain points** — durable rationale for the port → **WS-adr** (`2026-MM-DD-port-har-browse-to-rust.md`)
- **Working stance** ("starting point not a contract; rename aggressively; suggest improvements proactively") — methodology for port-style work → **Trans** for now; promotable to **WS-dev** if a corpus of similar work emerges. Pattern-of-one currently.
- **Strategy** (two-crate, foundation-first) — durable design rationale → **PL-design/two-crate-split.md** (overlap with `crate-architecture.md`; merge)
- **TOC + per-commit list** → **Trans** (this is the work map)
- **Success criteria** (byte-stable JSONL, BARRIER preserved, no Node runtime dep) — durable acceptance for the port effort → **WS-adr** (in the port ADR) and partially **HBR-design** (the crate's design goals)
- **Out of scope** (headless, bot-detection, crates.io publish) — durable design boundary → **PL-design/out-of-scope.md** + **HBR-design/out-of-scope.md** (or merge under a single workspace ADR)
- **End state** (sweep at 1300) → **Trans**

**Verdict:** 4 scope-homes. Charter as a whole stays transient; nuggets get
promoted now (the durable ones).

### `rust-port.kb/CLAUDE.md` (work-area maintenance guide)

- Pure maintenance guide for the work-area; transient with the work-area.

**Verdict:** **Trans** wholesale. If work-area relocates, this travels with it.

### `facts.kb/current-architecture.md`

- **Files list, behavior overview** — describes the current Node implementation → **HB-dev/architecture-current.md** (where it already implicitly is; could stay) OR delete after 1300.
- **Profile path scheme** (`${XDG_CACHE_HOME}/har-browse/profile/${profile}`, one per chatfs mount) — durable architectural decision; ALSO is normative for chatfs ("one profile per mount") → **WS-pol** or **HBR-design/cli-and-profile-scheme.md**.
- **Response-body / JSONL output shape** (`Network.responseReceived.params.response.body`, base64 encoding) — IS THE JSONL OUTPUT CONTRACT. Promotion target depends on Q1 below.
- **Invariants section** (BARRIER, causal watermark) — pointers to load-bearing semantics. To be re-encoded as `<scope>/barrier-invariants.md`/`causal-watermark.md` during commits 1000/1050. The reference / "these exist and are load-bearing" content → **HBR-design** or **WS-bg**.

**Verdict:** 3-4 scope-homes. The JSONL contract location is the central open
question (Q1).

### `facts.kb/ecosystem-survey.md`

Per the postmortem's worked example. Five sections, ≥4 scopes:

| Section | Content | Scope-home |
|---|---|---|
| Binary acquisition | CfT manager facts, arm64 caveat | **WS-bg/rust-chromium-automation.md** + **PL-dev/known-issues.md** (arm64 caveat) |
| Launch flags | `chrome-launcher` npm exports DEFAULT_FLAGS, ~27 entries, Google-maintained | **WS-bg/rust-chromium-automation.md** |
| CDP / target lifecycle | chromiumoxide auto-attach + recursive; issues #228/#280/#312 | **WS-bg** (capabilities) + **PL-dev/known-issues.md** (the open-issue watchlist) |
| Non-fits | headless_chrome, fantoccini, playwright-rust, playhard | **WS-bg** (durable: anyone surveying this niche needs the elimination reasoning) |
| Combination gap | no crate depends on both CfT + chromiumoxide | **WS-bg** (durable; justifies playwright-lite's existence even after the port) |

**Verdict:** 2 scope-homes (WS-bg + PL-dev). Big split. The "rejected
alternatives" reasoning also belongs in **PL-adr/2026-MM-DD-dependency-choices.md**
(decisions cross-ref the survey, not duplicate).

### `facts.kb/threat-model.md`

- **Givens** (headed-only, human-in-the-loop, per-mount profile, authenticated capture, non-adversarial) — these are project-wide and ALREADY OVERLAP with existing `WS-pol/policy-safe-automation-boundary.md` (which I read; covers the same stance under a different framing).
  - Resolution: don't duplicate. **Reconcile** with existing policy. Maybe add `WS-pol/policy-real-browser-first.md` as a narrower companion, or extend the existing policy doc to call out the headed-only stance explicitly.
- **Consequences for the port** (no webdriver patching, CfT acceptable, profile-per-mount ports verbatim) — design-constraint level → **PL-design** + **HBR-design**.

**Verdict:** 2-3 scope-homes. Plus a *reconciliation* with existing WS-pol.

### `facts.kb/unknown-unknowns.md`

- **Mitigated by chromiumoxide** (auto-attach, CDP transport) → cross-refs ecosystem-survey; partially **PL-design** (we accept these abstractions).
- **Mitigated by ~10 LOC of own code** (SingletonLock cleanup, first-run prefs, process tree, stderr noise, breakpad) — *foundational durable facts about running headed Chromium*. Anyone running Chrome will hit these → **WS-bg/chrome-headed-gotchas.md**. Also: each is a per-crate design choice for **PL-design** (or simply implemented in PL with comments).
- **Moot under our threat model** — cross-ref to threat-model.md. Stays as a section, doesn't move.
- **Monitored at runtime, not mitigated up-front** — cross-ref to assertion-strategy.md.

**Verdict:** 2 scope-homes (WS-bg + PL-design). Major durable extraction.

### `decisions.kb/port-to-rust.md`

Pure ADR-shaped content. Workspace-affecting (changes a package's language).

**Verdict:** 1 scope. **WS-adr/2026-MM-DD-port-har-browse-to-rust.md**.

### `decisions.kb/crate-architecture.md`

- **Two-crate split rationale** → **PL-design/two-crate-split.md** (durable design)
- **Workspace placement** (Cargo workspace, `packages/` layout) → already implied by repo. Mention in **WS-adr** as a footnote, or in the crate's design.kb.
- **Working names** → **Trans** (resolved by commit 0100).
- **Out of scope: publish to crates.io** → **PL-design/out-of-scope.md**.

**Verdict:** 3 scope-homes (PL-design dominant).

### `decisions.kb/dependency-choices.md`

- **Chosen deps** (CfT manager, chromiumoxide, vendored flags) → **PL-adr/2026-MM-DD-dependency-choices.md**
- **Rejected alternatives** → **PL-adr** (same ADR) cross-refs **WS-bg/rust-chromium-automation.md** for the survey content.
- **Why vendor vs subtree/submodule** → **PL-adr/2026-MM-DD-vendor-default-flags.md** (separate ADR; this is a vendoring-pattern decision distinct from picking deps).

**Verdict:** 1-2 PL-adrs. The audit recommends two separate ADRs since
"which deps" and "how to track vendored upstream" are independently citable.

### `decisions.kb/assertion-strategy.md`

- **The pattern** (defer + runtime-assert): *Is this workspace-wide policy or pattern-of-one?* Currently three instances, all inside playwright-lite. I lean **pattern-of-one**: keep with the instances, **PL-design/known-limitations.md**. Promote to **WS-pol** later if a second project adopts it. **Q2 below.**
- **The three concrete assertions** (flag drift, iframe-URL gap, chrome version drift) — per-crate (playwright-lite) durable limitations + their tripwires → **PL-design/known-limitations.md** (one entry per assertion, or a tiny sub-`.kb/`).

**Verdict:** 1-2 scope-homes depending on Q2.

### `decisions.kb/documentation-conventions.md`

- **`0N00` numbering, `## Outcomes` checkboxes, hand-off lifecycle, per-commit not per-session** — conventions for *this work-area*. They could generalize to any port-style work, but no second instance exists. Keep with the work-area for now.
- The "what lives where" table → **Trans** (will become stale immediately after this refactor).

**Verdict:** **Trans** wholesale. Update the table after the refactor.

### `procedures.kb/{consume-handoff,end-of-commit,session-start}.md`

All three reference port-specific paths (`commits.kb/`, `handoffs.kb/`,
`rust-port.md`) and trigger on port-stage states. Procedure shape is reusable
but content is hard-coded to the work-area.

**Verdict:** **Trans** for all three.

### `handoffs.kb/CLAUDE.md`

Currently empty collection. Maintenance guide stays with the work-area.

**Verdict:** **Trans**.

### `commits.kb/*.md` (15 files)

Each is per-commit narrative (Plan, Refs, Outcomes, Notes). Transient by
design. They reference durable contracts (`dev.kb/jsonl-schema.md`, etc.) but
the doc itself is not durable.

**Verdict:** **Trans** for all 15.

Exception: commit docs `0750`, `1000`, `1050` *produce* durable contracts.
The commit doc remains transient; the *output artifact* (the contract doc)
must have a permanent home decided before those commits land — that's the
todo's original concern. **Q1 resolves this.**

### `commits.kb/CLAUDE.md`

Maintenance guide for the commits collection. **Trans**.

## Cross-cutting promotion plan (synthesis)

What gets *written* and *where*, distilled from the audit:

### Workspace-level (durable)

- **`docs/dev/adr/2026-MM-DD-port-har-browse-to-rust.md`** — port decision. Sources: `decisions.kb/port-to-rust.md` + charter's "Why" / success criteria / out-of-scope.
- **`docs/dev/background.kb/rust-chromium-automation.md`** — ecosystem facts (CfT, chrome-launcher npm, chromiumoxide, non-fits, combination gap). Sources: `ecosystem-survey.md` (most of it).
- **`docs/dev/background.kb/chrome-headed-gotchas.md`** — SingletonLock, first-run prefs, process tree (`setsid`/`killpg`), stderr noise, breakpad. Sources: `unknown-unknowns.md` (the "10 LOC of own code" section).
- **Reconcile** `WS-pol/policy-safe-automation-boundary.md` with the threat-model.md content. Likely a small extension to the existing doc; not a new file.

### `packages/playwright-lite/` skeleton (durable, empty-OK)

- `CLAUDE.md` (crate entry)
- `README.md` (placeholder)
- `design.kb/two-crate-split.md` — from `crate-architecture.md` + charter Strategy
- `design.kb/out-of-scope.md` — from charter + crate-architecture (headless, bot-detection, crates.io publish)
- `design.kb/known-limitations.md` (or sub-`.kb/`) — three deferred items from `assertion-strategy.md`
- `adr/2026-MM-DD-dependency-choices.md` — from `dependency-choices.md` (chosen + rejected, cross-ref WS-bg for the survey reasoning)
- `adr/2026-MM-DD-vendor-default-flags.md` — from `dependency-choices.md` ("Why vendor")
- `dev.kb/known-issues.md` — chromiumoxide #228/#280/#312, CfT arm64 caveat (per-crate watchlist)
- `dev.kb/CLAUDE.md`

### `packages/har-browse-rs/` skeleton (durable, empty-OK)

- `CLAUDE.md` (crate entry)
- `README.md` (placeholder)
- `design.kb/cli-and-profile-scheme.md` — XDG path scheme, `--profile` default
- `design.kb/done-button-termination.md` — design choice (vs SIGINT / window close)
- `dev.kb/` — populated by commits 0750/1000/1050 with `jsonl-schema.md`, `barrier-invariants.md`, `causal-watermark.md` (BUT see Q1)
- `dev.kb/CLAUDE.md`

### Transient work-area (residual after promotions)

- `rust-port.md` (charter, slimmed — durable nuggets moved out, pointers to new homes added)
- `rust-port.kb/CLAUDE.md` (updated lifecycle)
- `rust-port.kb/commits.kb/` (15 files unchanged in body; Refs updated to new permanent homes)
- `rust-port.kb/handoffs.kb/` (CLAUDE.md only currently)
- `rust-port.kb/procedures.kb/` (3 files; paths updated)
- `rust-port.kb/decisions.kb/documentation-conventions.md` (table refreshed to match new layout)

`facts.kb/`, `decisions.kb/{port-to-rust,crate-architecture,dependency-choices,
assertion-strategy}.md` are emptied — their content has all moved. Either
delete those files now or leave them as one-line redirect stubs until 1300
sweep removes everything. Leaning **delete now** (cleaner; commits.kb/Refs
already updated to new homes).

## Where the transient work-area lives (the todo's original question)

After the promotions above, residual transient content is small but
multi-crate-scoped. Three candidates:

| Option | Pros | Cons |
|---|---|---|
| **(A) Workspace-root `dev.kb/rust-port.kb/`** | Matches scope (workspace-spanning); creates a useful WS-dev container; mirrors `docs/dev/design-incubators/` precedent for cross-cutting work | Requires creating workspace `dev.kb/`; one-shot occupant |
| **(B) Crate-local** (one of the two new crates) | Trivially located | Wrong scope: work spans both crates; arbitrary which one wins |
| **(C) `docs/dev/design-incubators/rust-port/`** | Existing structure; no new container needed | "design" misframes implementation work; incubators are for design exploration with prototypes, not for porting an existing implementation |

**Recommendation: (A)** workspace-root `dev.kb/rust-port.kb/`, with charter
becoming `dev.kb/rust-port.md` (or `dev.kb/rust-port.kb/CHARTER.md`). The
workspace `dev.kb/` exists from this moment forward; if future workspace-
spanning dev work appears, it has a home; if not, the directory disappears
at 1300 with the rest.

## Sequencing (proposed execution order)

Each step is reviewable on its own; nothing destructive until late.

1. **Audit review.** This document. Stop and get feedback before anything below.
2. **Resolve Q1, Q2** (see below).
3. **Create empty skeletons** for `packages/playwright-lite/` and `packages/har-browse-rs/` (just `CLAUDE.md`, `README.md`, empty `design.kb/{CLAUDE.md}`, `dev.kb/{CLAUDE.md}`, `adr/`). No content yet.
4. **Create workspace `dev.kb/`** with a CLAUDE.md describing the dir's purpose.
5. **Write the promoted durable docs** (one commit per logical group):
   - WS-adr port-to-rust
   - WS-bg rust-chromium-automation + chrome-headed-gotchas
   - PL design.kb/{two-crate-split, out-of-scope, known-limitations}
   - PL adr/{dependency-choices, vendor-default-flags}
   - PL dev.kb/known-issues
   - HBR design.kb/{cli-and-profile-scheme, done-button-termination}
   - WS-pol reconciliation (or note in `dev.kb/` that the existing policy covers it)
6. **Move work-area** from `packages/har-browse/dev.kb/rust-port.{md,kb}/` to `dev.kb/rust-port.{md,kb}/`.
7. **Update commit-docs `Refs:`** to point at new permanent homes.
8. **Delete emptied source files** in the old `facts.kb/` / `decisions.kb/`.
9. **Update `documentation-conventions.md`** table to reflect new layout.
10. **Update `packages/har-browse/dev.kb/CLAUDE.md`** — remove rust-port collection mention (or change to "moved to workspace `dev.kb/`").
11. **Update root and har-browse `CLAUDE.md`** with discoverability pointers to the new homes.

Steps 3-5 can run as one stack of commits with `--fixup` where reasonable.

## Open questions (for user)

### Q1: Where does `jsonl-schema.md` live?

This contract is produced by commit 0750 and consumed by commit 0800. After
1300 it's a permanent artifact.

- **(a) `packages/har-browse-rs/dev.kb/jsonl-schema.md`** — implementer-side. Fits if har-browse-rs is the only BB1 capture.
- **(b) `docs/dev/design.kb/050-components.kb/`** or similar workspace-level — architectural contract between BB1 (capture) and BB2 (extraction). Fits the project's black-box decomposition pattern.
- **(c) Workspace-root `dev.kb/jsonl-schema.md`** — cross-package contract, but at the dev (how-we-build) layer rather than design (what-it-is).

I lean **(b)**: chatfs's BB1→BB2 seam is architectural; the JSONL shape is
the contract between black boxes; multiple BB1 implementations (claude.ai,
chatgpt.com, other sites) are foreseeable. Promotes the schema out of the
implementer.

Same question applies to `barrier-invariants.md` / `causal-watermark.md`
from commits 1000/1050. I lean: these are **HBR-design** (capture-specific)
not workspace-architectural — they encode how *one* capture implementation
maintains ordering correctness; the JSONL output already commits to the
externally-observable result.

### Q2: Is "defer + runtime-assert" workspace-policy or pattern-of-one?

Currently three instances, all in `playwright-lite`. If you'd cite this
pattern elsewhere in chatfs ("here's how we handle deferred limitations"),
promote to `WS-pol/policy-defer-with-runtime-assertion.md` now. If not,
keep folded into `PL-design/known-limitations.md` for now and promote later
when the second instance appears.

I lean **pattern-of-one for now**. Two reasons: (1) the postmortem flags
this exact question as "unverified"; (2) the runtime-assertion machinery
is concrete (Rust panics/assertions in test target), which doesn't transfer
verbatim to other languages in the workspace.

### Q3: How to reconcile threat-model.md with the existing `policy-safe-automation-boundary.md`?

Three options:
- Extend the existing policy doc inline with a "headed-only / non-adversarial"
  section.
- Add a sibling `policy-real-browser-first.md` (narrower; consumed by capture
  components specifically).
- Leave the existing policy alone; let har-browse-rs cite it directly without
  promoting threat-model.md content.

I lean **extend the existing policy** (option 1). The two stances are
sub-aspects of the same boundary.

### Q4: Naming of the new crates — really `playwright-lite` and `har-browse-rs`?

Charter says working names, decided at commit 0100. For *kb* purposes,
naming the skeleton dirs now requires picking. Options:

- Keep working names `playwright-lite` / `har-browse-rs`. Rename later if
  needed (kb path moves with the rename).
- Pick the postmortem's `rs-playwright-lite` / `rs-har-browse`.
- Defer skeleton creation until 0100 picks names.

I lean **keep working names** — the postmortem's `rs-` prefix is the user's
intuition but not yet decided; rename is cheap once chosen; deferring
skeletons blocks the audit's whole "empty parent dirs are valid" insight.

## Confidence and uncertainties

- **High confidence (>90%)**: per-file scope splits for `ecosystem-survey.md`, `current-architecture.md`, `unknown-unknowns.md`, `port-to-rust.md`, `crate-architecture.md`, `dependency-choices.md`.
- **Medium confidence (~75%)**: assertion-strategy split (Q2 dependency).
- **Lower confidence (~65%)**: jsonl-schema location (Q1); precise WS-pol reconciliation shape (Q3).
- **Things I haven't verified**: whether the existing `policy-safe-automation-boundary.md` already implies threat-model.md content fully (I only read first 40 lines); whether `docs/dev/design.kb/050-components.kb/` is the right home for cross-component contracts (didn't open it).

## Things explicitly NOT in this audit

- Any moves, edits, or deletions to actual files.
- Any new files outside `trash/`.
- Any directory creations (incl. skeletons).
- Final names for the new crates.
- Decisions on Q1-Q4.

Next step: review this audit. Resolve open questions. Then execute the
sequencing plan, one step at a time.
