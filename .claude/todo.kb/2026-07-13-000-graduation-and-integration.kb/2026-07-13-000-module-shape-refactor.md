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
layout — see note below the tree). Shared cross-provider primitives stay
at the package root; providers nest one level under a `provider/`
subpackage (ready for the future `chatfs.providers` entry-point split,
and the natural future home for a formal base-adapter module); nouns are
subpackages within each provider, matching the CLI command path and
`package-division.md`'s `chatfs.provider.chatgpt.conversation…` example.
Locator+verb join as one leaf module filename — no separate locator
directory; only 2 verbs per locator today, an extra level buys nothing.

    chatfs/
      json.py                  # typed JSON + jsonl serialization (dump_jsonl moves here)
      pluck.py                 # CDP filtering: iter_responses_matching, pluck, run_pluck
      capture.py               # sources: browse (har-browse wrapper) + capture()
                               # (composes browse+pluck, lands exhaust per layout)
      layout.py                # path vocabulary + placement only: DATA_DIR_NAME,
                               # safe_filename, time_dir_for, chat_dir_for,
                               # resolve_chat_dir, place_meta
      render.py
      url_browse.py            # provider-agnostic url-browse helpers (was chatfs_url_browse.py)
      provider/
        claude/
          layout.py            # provider adapter minus wire knowledge: _created,
                               # capture/place_meta wrappers, url_for/uuid_from_url
                               # (consolidating the copies in url_browse/url_render;
                               # kills url_trash's script-importing-script)
          pluck.py             # wire knowledge: URL regexes, pluck_conversation,
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
- [ ] Discuss with user (their request, 2026-07-17) before any moves:
      better separation of pure vs side-effected code in the module
      organization. The amended tree separates *concerns* but not
      *purity* — e.g. `pluck.py` would hold the pure generator
      (`iter_responses_matching`) alongside the file-teeing drivers
      (`pluck`/`run_pluck`). The discussion may re-partition the tree;
      treat the Proposed Solution as a checkpoint until it happens.
- [ ] Move one provider family end-to-end (suggest claude — has the most
      tests), tests green, as the template. While moving each family:
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
