---
managed-by: Skill(llm-subtask)
cost-benefit-sweh:
  timebox:
    "@value": 1.0
    rationale: |
      File-level estimate for a 6-item rollup that's mostly tracking
      upstream skill work. Only the mockup-chatgpt rename is actual
      tactical work here. (2026-07-13: the graduation & integration
      umbrella carries its own ~40h rollup in its kb file — not counted
      here.)
  benefit-2w:
    "@value": 0.5
    rationale: |
      Most payoff is double-counted in upstream items (llm-kb/todo.md,
      rust-port kb scope refactor). Local payoff is the mockup-chatgpt
      rename plus better visibility into cross-repo blockers.
---

# Tactical Tasks

Driver: [Harmonize with llm-* skills](todo.kb/2026-01-02-000-harmonize-with-llm-skills.md) — most done; chatfs-local remaining items below.

## Graduation & integration — active arc

- [ ] [Graduation & integration umbrella](todo.kb/2026-07-13-000-graduation-and-integration.md)
      — incubator → `packages/chatfs-cli` → `chatfs mount`. Six children
      with `blocked-by` edges in
      `todo.kb/2026-07-13-000-graduation-and-integration.kb/`; own
      cost-benefit rollup. Planned 2026-07-13 — devlog
      `docs/dev/devlog/2026-07-13-000-graduation-and-integration-planning.md`;
      decided names/conventions in
      `docs/dev/design.kb/040-design.kb/package-division.md`.
- [x] Re-cut `docs/how-to-chatfs.md` at graduation — every command in it is
      `python -m chatfs.provider.<name>...` run from the incubator dir, and
      becomes wrong the moment `packages/chatfs-cli` (or `chatfs mount`) is the
      real entry point. Same pass should de-overlap it from the incubator
      README (user-facing vs stage-by-stage). Written 2026-07-27 — devlog
      `docs/dev/devlog/2026-07-27-000-First-user-facing-doc--how-to-chatfs.md`.
      Re-cut 2026-08-07 with child 001: installed kebab commands, required
      `--cache <dir>`, package README carries the stage-by-stage anatomy.

## chatfs-cli-mockup — next sessions

Plan from 2026-05-05 design.kb consolidation. Order is dependency-driven; 1-2 are blocking, 3-4 are deferrable. Incubator-tactical breakdowns re-homed 2026-08-07 to `packages/chatfs-cli/.claude/todo.kb/` (child 001).

1. [x] **`.chat/$UUID/` implementation.** Landed 2026-05-08; see devlog `2026-05-08-000-chatfs-mockup-chatgpt-chat-as-directory-implementation.md`.
2. [x] **README rewrite + end-to-end test.** Landed 2026-05-08; live URL test passed (188 messages / 129 turns initial, 262 / 206 follow-up). See devlogs `2026-04-29-000` and `2026-05-08-001`.
3. [x] **Noun-verb sub-kb.** Landed 2026-05-11 as `design.kb/040-design.kb/cli-command-shape.kb/` (partition-prefix scope, Hive-style `key=value` naming; the kb moved 2026-08-08 to `packages/chatfs-cli/design.kb/`). See devlog `2026-05-11-000-chatfs-mockup-chatgpt-cli-command-shape-kb.md`.
4. [x] [Rename incubator to chatfs-cli-mockup](todo.kb/2026-05-11-000-rename-incubator-to-chatfs-cli-mockup.md) — precursor to multi-provider sketch; current name encodes a single provider. Done 2026-07-10: `git mv` + full reference sweep (remaining old-name hits are historical: devlog filenames/bodies, the ADR title); README closing reframed to the `$REPO/lib/chatfs/` graduation target. Verified: basedpyright 0/0/0, pytest 19/19, no symlink targets the old path.
5. [x] **Multi-provider sketch** (deferrable). Scope B from 2026-05-11 conversation: hand-prepare a Claude data-export-derived `chatfs.demo/claude/.chat/$UUID/` and run splat + render through it; no live BB1 capture from claude.ai yet. Tests the parent project's `provider-plugin-model.md` against a second provider in practice. Also the natural moment to promote the incubator's `provider-plugin-model.md` symlink to a real entry or sub-kb. Superseded 2026-07-10: the claude provider landed via live BB1 capture (MVP closed 2026-05-11, devlog `2026-05-11-001`) — stronger than the hand-prepared export sketch — and AI Studio followed as a third provider (2026-06-20..07-03); the `provider-plugin-model.md` promotion landed 2026-07-09 (devlog `2026-07-09-000`). Nothing of this scope remains.

## Chatgpt provider follow-ups (2026-08-16 splat fold-in)

- [ ] [bukzor.chatgpt-export package fate](todo.kb/2026-08-17-000-bukzor-chatgpt-export-package-fate.md)
      — `har2jsonl.py` is the only thing left in that package with no
      current caller; decide keep/fold-in/delete.
- [ ] `pytest-pyright`'s file-collection check is cwd-relative to
      `typesafety/`, not repo-root-relative — the float-rejection
      typesafety test (now at `packages/chatfs-cli/typesafety/`) has
      never actually run under the documented root-level `pytest .`
      workflow, only `cd <package> && pytest typesafety`. Either fix the
      plugin invocation (a `--pyright-dir` per package, or a root
      conftest hook) so root `pytest .` really exercises it, or add the
      caveat to `HACKING.md`'s testing section so the gap is at least
      visible.

## Index pipeline follow-ups (2026-08-27)

- [ ] Nothing drives `index splat`'s `main()` under test. Its stdout
      contract (one `{id, title, chat_dir, view}` per chat placed) and
      its first-sight dedup rule were verified once, by hand, against a
      throwaway fake `har-browse` in `trash/`; `place_test.py` only
      covers `Placement` itself. Feed each provider's splat a two-page
      jsonl fixture with one item repeated across pages, assert the
      records on stdout.
  - [ ] claude — overlapping pages are expected, so the repeat must be
        re-written but announced only once
  - [ ] chatgpt — asserts no duplicate uuid; cover that the assertion
        still fires rather than silently emitting twice
  - [ ] aistudio — claude's dedup shape, chatgpt's item wrapper

## Provider-agnostic CLI surface (2026-08-28)

The cache root holds every provider as of `befa423`, so a chat's provider is
now a path segment and a URL's provider is its host — both knowable without
the user naming a driver. Diagnosed from a live failure: the claude driver
run against a chatgpt path asserts on `meta.json`'s shape and dumps the whole
dict instead of saying which driver to use.

- [x] Demote the provider to an ordinary path segment in command names:
      `chatfs-<p>-<noun>-<verb>` → `chatfs-provider-<p>-<noun>-<verb>`. Makes
      `cli-command-shape.md`'s stated kebab-name-equals-module-path rule true
      (the module path already carries `provider`; the command silently elides
      it), and frees the bare `chatfs-<noun>-<verb>` names for the dispatcher.
      `[project.scripts]` and docs only — no runtime coupling, since every
      occurrence under `lib/` is a docstring and stages invoke each other by
      module path. Done 2026-08-28: 30 entry points renamed, no stale name
      left in `.venv/bin/`. Historical hits left stale by the repo's own
      precedent — devlog bodies, and the two completed `todo.kb/` children
      that record the 2026-08-07 naming decision.
- [ ] `chatfs-conversation-url-<verb>` — dispatch on URL host
      (`claude.ai` / `chatgpt.com` / `aistudio.google.com`). Total and
      injective; every provider already has `uuid_from_url`.
- [ ] `chatfs-conversation-path-<verb>` — dispatch on the provider segment of
      the resolved chat dir. Deliberately *not* a `meta.json` shape sniffer:
      chatgpt's and aistudio's `is_index_item` differ only in which second
      time field they carry and its JSON type, and the chatgpt half is an
      upstream payload `path-ownership.md` requires we keep verbatim, so
      shape-disjointness is a coincidence we don't control.

## Transcript consumer ergonomics

- [ ] [Transcript consumer ergonomics: toc, message access, export verify](todo.kb/2026-08-08-000-Transcript-consumer-ergonomics--toc--message-access--export-verify.md)
      — requirements filed 2026-08-08 from the consumer side (agent
      serializing/auditing the llm-stet export with grep/sed): message
      index, single-message access, intra-export link verification.
      Command spelling deferred to `packages/chatfs-cli/design.kb/`.

## Corpus view mechanism

- [ ] [Generalize the Created= symlink-view mechanism; add a pulled/unpulled status view](todo.kb/2026-08-17-001-Generalize-the-Created--symlink-view-mechanism--add-a-pulled-unpulled-status-view.md)
      — extends `chatfs.layout`'s existing view-tree pattern to a second
      attribute chatfs already has the data for.

## Rust port — kb scope refactor

- [ ] [Execute the rust-port kb scope refactor](todo.kb/2026-05-16-000-execute-rust-port-kb-scope-refactor.md) — 9 steps; must land before commits 0750/1000/1050. Layered with 2026-05-21 meta-planning evolutions (see todo's "Additional decisions" section).
- [ ] [Polyglot package dir naming — sweep existing packages](todo.kb/2026-05-16-001-polyglot-package-dir-naming-sweep.md) — depends on execute-rust-port above
- [ ] **Update `packages/har-browse/dev.kb/rust-port.md` charter:** insert commit `0050` (blackbox `.spec.mjs` → CLI conversion + baseline capture) before `0100` scaffold; record commits `0025`/`0035` if diagnostic-events design and Node-side emission want separate commits. Source: `.claude/decision.kb/test-conversion-precedes-port-scaffold.md`.
- [ ] **Pre-port testing infrastructure** (Phases C/D/E) — tracked at `~/.claude/sessions.kb/har-browse-rust-port-pre-port-infrastructure.md`. Must precede commit `0800` (cdp-jsonl contract freeze) at minimum.

## Doc & schema hygiene

- [ ] [Clear the twelve frontmatter validation errors](todo.kb/2026-08-22-000-clear-the-twelve-frontmatter-validation-errors.md)
      — surveyed 2026-08-22 as twelve errors in five causes; down to
      nine on 2026-08-27, the modeline ruling having cleared the three
      `todo.md` roll-ups upstream. Seven of the nine are fixable here (a
      missing `background.jsonschema.yaml`, a `kind` enum, one legacy
      field shape); the `status` enum pair stays blocked on
      bukzor-agent-skills. Listed here 2026-08-27, having been invisible
      to every sweep in between.
- [ ] Four `> [!TODO]` callouts in
      `packages/chatfs-cli/design.kb/040-design.kb/cli-command-shape.kb/noun=conversation.kb/verb=render.md`
      carry no one-line title after the bracket, which is what makes a
      bare `grep '\[!TODO\]'` read like a todo list (`Skill(llm-design-kb)`).
      Title each; the fourth needs its body's opening clause rewritten
      so the title isn't duplicated. They are the repo's only untitled
      markers.

## Deferred

- [x] Fix 4 frontmatter violations in `docs/dev/aistudio-schema/discourse.kb/` — drift accumulated 2026-06-23..08-08 while the schema symlinks dangled (revealed when the `$ref: skill://` stubs restored validation, commit 9324dba): `sources.kb/{bundle-audit,live-replay-probe,rosetta-correlation-experiment}.md` use `kind: investigation` (not in the canonical enum — may want an enum addition in llm-discourse-graph instead of a content edit), and `questions.kb/how-does-this-serve-chatfs.md` has an unexpected `status:` plus a date-typed `resolved:` where the canonical wants a string. Superseded 2026-08-27: the 2026-08-22 fleet-wide sweep re-surveyed the same drift as part of a twelve-error picture — all four of these are in it. Live entry under "Schema & frontmatter hygiene" above.
- [ ] Create `docs/dev/milestones.kb/` — double-blocked (no milestone content yet; skills-repo pattern not defined)
- [x] Fix pre-existing basedpyright errors in docs/ exploration scripts (3 as of 2026-08-08: implicitly-relative `convert` imports in `docs/dev/aistudio-schema/rosetta/{correlate,verify}.py`; unresolvable vendored `claude_api` import in `docs/dev/design-incubators/fork-representation/investigate-forks.py`) — deliberately left visible rather than excluded when the `**/docs` pyright exclude was narrowed to vendored code only. Done 2026-08-08: rosetta imports resolved via root `executionEnvironments`; `investigate-forks.py` rewritten to file/stdin input (dead `claude_api` fetch path removed). Repo-wide pyright 0/0 — devlogs `2026-08-08-001`, `2026-08-08-003`.
- [x] Drop the typed-json `[tool.uv.sources]` git pins — root `pyproject.toml` plus the PEP 723 blocks in `docs/dev/aistudio-schema/{body-shape,extract-bundles}.py` and `docs/dev/design-incubators/fork-representation/investigate-forks.py`. Done 2026-08-08: publication landed as **`python-typed-json`** (PyPI blocked `typed-json` — name collision with third-party `typedjson`; my "name confirmed free" was wrong at upload time). Import name is unchanged (`typed_json`); dependency renamed in `packages/chatfs-cli/pyproject.toml` and the three PEP 723 blocks, sources tables deleted.

## Upstream (mirrors of skills-repo todos; kept here for visibility)

- [ ] llm-kb: cross-kb cooperation conventions (symlinks, cross-kb references, maintenance-traversal scope; llm-design-kb layer-crossing policy rider) — tracked at `~/.claude/skills/llm-kb/.claude/todo.kb/2026-07-13-000-cross-kb-cooperation-conventions.md`; this repo proceeds on interim conventions (see graduation umbrella)
- [ ] llm-kb: complete `.d → .kb` rename in `complete-example/` — tracked at `~/.claude/skills/llm-kb/.claude/todo.kb/2026-01-02-000-complete-d-to-kb-rename.md`
- [ ] llm-collab: define `milestones.kb/` pattern in skeleton — tracked at `~/.claude/skills/llm-collab/.claude/todo.kb/2025-12-11-000-update-skeleton-to-match-docsdev-pattern-from-git-partial.md`
- [x] llm-subtask: task-graph relations now modeled (2026-07-09), resolved per-field rather than one field per name. Hard dependency: canonical `blocked-by` field added to the llm-subtask base schema (`depends`/`depends-on` renamed to it). Parent/subtask-of: sub-kb nesting -- `2026-01-02-002` moved under `2026-01-02-000-harmonize-with-llm-skills.kb/`, `parent:` dropped. `supersedes-question-from`: chatfs-local `#base` extender in `.claude/todo.jsonschema.yaml`. Root stub no longer held back; `llm.kb-validate .claude` green (33 files).
