---
managed-by: Skill(llm-subtask)
related-effort: docs/dev/design.kb/040-design.kb/package-division.md
cost-benefit-sweh:
  timebox:
    "@value": 4.0
    rationale: >
      ~30 scripts, mostly mechanical moves + import rewrites once the
      layout is settled; tests already exist and gate each family.
      Overrun signals the layout needs rethinking, not more pushing.
    confidence: tentative
  benefit-2w:
    "@value": 1.0
    rationale: >
      Ends sibling-import fragility and per-incubator pyright scoping;
      precondition for everything downstream.
    confidence: tentative
---

# Module-shape refactor — flat scripts → `chatfs` package (in place)

**Priority:** High — first child of the graduation umbrella.
**Complexity:** Medium
**Context:** `docs/dev/design-incubators/chatfs-cli-mockup/` holds ~42 flat
sibling-importing scripts (`chatfs_<provider>_<noun>_<verb>.py`, shared
`chatfs_layout.py` / `chatfs_render.py` / `chatfs_json.py` — all Python as
of 2026-07-15's jq/sh port, no `*.jq`/`.sh` left). Naming design: the
incubator's
`design.kb/040-design.kb/cli-command-shape.md`; shared/provider split:
its `provider-plugin-model.md`.

## Problem Statement

Scripts import siblings by flat module name, so they only run from the
incubator directory, need a scoped pyright `executionEnvironments`
workaround, and can't be packaged. Restructure into an importable `chatfs`
package *in place* (the move to `packages/` is the next child).

## Proposed Solution

Settled 2026-07-14; amended 2026-07-17 (pluck/capture factored out of
layout) and 2026-07-19 (purity partition: `shell/` subpackage — see the
dated rationale notes below the tree). Shared cross-provider primitives stay
at the package root; providers nest one level under a `provider/`
subpackage (ready for the future `chatfs.providers` entry-point split,
and the natural future home for a formal base-adapter module); nouns are
subpackages within each provider, matching the CLI command path and
`package-division.md`'s `chatfs.provider.chatgpt.conversation…` example.
Locator+verb join as one leaf module filename — no separate locator
directory; only 2 verbs per locator today, an extra level buys nothing.

    chatfs/
      json.py                  # typed JSON + jsonl serialization (dump_jsonl moves here)
      pluck.py                 # pure CDP filtering: iter_responses_matching
                               # (the file-teeing pluck/run_pluck drivers → shell/capture.py)
      layout.py                # pure path vocabulary: DATA_DIR_NAME, safe_filename,
                               # time_dir_for, chat_dir_for, data_dir_for
                               # (the placement/fs half → shell/place.py)
      render.py
      url_browse.py            # provider-agnostic url-browse helpers (was chatfs_url_browse.py)
      shell/                   # the imperative shell (bourne pun intended): the only
                               # modules whose top level may import os/sys/subprocess/…
        sh.py                  # was chatfs_sh.py
        atomic.py              # was chatfs_atomic.py
        locks.py               # was chatfs_locks.py
        capture.py             # browse() (har-browse wrapper), pluck/run_pluck tee
                               # drivers, capture() (composes browse+pluck, lands
                               # exhaust per layout)
        place.py               # place_meta, link_data_dir, resolve_chat_dir,
                               # purge_view_symlinks — the fs half of old chatfs_layout
      provider/
        claude/
          layout.py            # pure provider adapter: _created, url_for/uuid_from_url,
                               # label conventions (consolidating the copies in
                               # url_browse/url_render; kills url_trash's
                               # script-importing-script). capture/place_meta wrappers
                               # dissolve — leaf main()s call shell.capture/place with
                               # pure provider config directly
          pluck.py             # wire knowledge, pure data→data: URL regexes, pluck_conversation,
                               # pluck_index_pages; stdin→stdout main with a
                               # {conversation,index} selector restores the
                               # re-pluck-without-Chromium seam that the jq→Python
                               # port removed (stdio-pipeline-shape.md claims it)
          types.py
          conversation/
            url_browse.py
            url_render.py
            path_browse.py
            path_render.py
            render.py
            render_test.py
            splat.py
            splat_test.py
          index/
            splat.py
            browse.py          # was chatfs_claude_index_browse.py
        chatgpt/  ...          # same shape, no conversation/splat.py
        aistudio/ ...          # same shape, + conversation/massage_json.py;
                               # pluck.py also carries the JSPB envelope guard/flatten

Amendment rationale (2026-07-17): post-port `chatfs_layout.py` mixes
three concerns under one name — path vocabulary/placement (layout
proper), CDP filtering, and capture orchestration — and the provider
`*_layout.py` modules likewise carry URL regexes and pluck functions
that are wire-format knowledge, not layout. The original tree folded
pluck into layout ("no separate file"); reversed — the `.jq` files'
file-level identity for the filter stage was worth keeping, only their
implementation language wasn't. Import layering runs strictly downward:
json → types → pluck → layout → {capture, render} → leaves; `capture.py`
sits above both pluck and layout so layout stays subprocess-free and
pluck stays layout-free (render sits at capture's level: it consumes
layout names as data, never touches the filesystem).

Amendment rationale (2026-07-19, discussed with user — closes the
gating discussion step below): the concern split is now also a purity
split. Everything outside `shell/` is pure; side effects — fs reads
included — are limited to `main()` functions there, and impure imports
(`os`, `sys`, `subprocess`, `shutil`, …) appear only inline inside
`main()`, never at module top level. We mark the impure minority, not
the pure majority: a `pure/` subtree was considered and rejected —
most pure code lives in provider leaves whose module path must match
the CLI command path, so a `pure/` tree either mirrors the whole
provider tree or fails to contain most of the pure code. `shell/`
(named for both senses: imperative shell, bourne shell — `sh.py` lives
there) collects the intrinsically impure trio (sh/atomic/locks) plus
the impure halves of pluck (tee drivers → `capture.py`) and layout
(placement → `place.py`); the 2026-07-17 tree's provider
capture/place_meta wrappers dissolve into leaf `main()`s calling shell
functions with pure provider config. Layering supersedes 2026-07-17's:
pure core `json → types → pluck → layout → render`, strictly downward;
`shell/` above the core; leaf `main()`s on top. Enforcement is
documentary, not mechanical: the `chatfs/__init__.py` and
`chatfs/shell/__init__.py` docstrings state the invariant (the agreed
~90% solution); an AST-scanning purity gate was deliberately deferred
— recorded in
`.claude/ideas.kb/2026-07-19-000-Purity-gate--AST-scan-for-shell-only-imports.md`.
A shape this enables, adopted per family as it moves (not mandated up
front): splat/writer stage functions yield `(relpath, content)` pairs
and `main()` does the writes, dropping tmp-dir test fixtures.

Bare-verb leaves remain invocable (thin executable shims or `python -m`)
so the pipe surface and delegation orchestrators keep working throughout
— the driver-model decision (one importable stage function, two thin
surfaces) is the guide.

## Implementation Steps

- [x] Port `.jq`/`.sh` pipeline scripts to Python — landed 2026-07-15, see
      devlog
      `docs/dev/design-incubators/chatfs-cli-mockup/devlog/2026-07-15-000-port-jq-sh-pluck-pipeline-to-python.md`
      (extracted 2026-07-14 as its own tracked task, now closed and
      deleted). No `*.jq`/`.sh` remain in the incubator.
- [x] Discuss with user (their request, 2026-07-17) before any moves:
      pure vs side-effected separation. Resolved 2026-07-19: `shell/`
      subpackage + main()-only side effects + inline impure imports;
      docstring enforcement, AST gate deferred to ideas.kb. Tree and
      rationale above amended in place — the Proposed Solution is no
      longer a checkpoint.
- [x] Write the purity-invariant docstrings in `chatfs/__init__.py` and
      `chatfs/shell/__init__.py` as part of the package skeleton — this
      is the agreed enforcement mechanism, a deliverable, not an
      afterthought. Landed 2026-07-19.
- [ ] Move one provider family end-to-end (suggest claude — has the most
      tests), tests green, as the template. 2026-07-19: `git mv` pass
      landed for all three providers + shared core (not just claude —
      the shared core is imported by all three, so a claude-only move
      would break chatgpt/aistudio's sibling-imports just the same;
      moving everything in one mechanical commit was cheaper than two).
      Zero content edits in that commit — all sibling-imports
      (`chatfs_layout`, `chatfs_json`, etc.) are broken repo-wide until
      the edit pass(es) land, starting with claude per the template
      plan. While moving each family:
      convert orchestrators' subprocess calls to sibling splat/render
      stages into in-process imports of the stage functions
      (driver-model.md's open [!TODO] — its named tracker, the
      shared-code-among-providers question, closed 2026-07-12 without
      landing it; this todo is now the tracker).
- [ ] Sweep remaining families + shared modules; delete flat scripts as
      each family lands.
  - [ ] Decide chatgpt splat's home during the sweep: today it's the one
        stage living outside the incubator (`chatgpt-splat` from
        `packages/bukzor.chatgpt-export`, invoked as a subprocess) while
        claude/aistudio splats are local scripts — fold it in as
        `provider/chatgpt/conversation/splat.py`, or record why it stays
        external.
- [ ] Update the incubator README's "Run it" section to the new
      invocations.

## Success Criteria

- [ ] No `chatfs_*`-prefixed flat scripts remain; every stage importable
      as `chatfs.…` and runnable from any cwd.
- [ ] Full test suite + basedpyright clean; live end-to-end run of one
      provider's url-browse against the demo tree.

## Notes

Atomic-regeneration (incubator first-priority todo) lands before or with
this — promoted code should be born compliant.

`.data/` scratch convention (decided 2026-07-14, see
`docs/dev/technical-policy.kb/path-ownership.md`'s `.data/` section):
only `meta.json`/`conversation.json`/`cdp.jsonl` are contract names at
`.data/` top level; every top-level contract name `X` reserves the
sibling `X.d/` for scratch related to producing/checking it (e.g. a
pre-normalization pluck goes in `conversation.json.d/`, not a new
top-level name). Not yet implemented — a candidate to land with this
refactor (same file-touching motion) rather than as a separate pass,
but not a hard precondition the way atomic-regeneration is.
