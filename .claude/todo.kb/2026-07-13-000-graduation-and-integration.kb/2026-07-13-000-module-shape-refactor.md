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
**Context:** `docs/dev/design-incubators/chatfs-cli-mockup/` holds ~30 flat
sibling-importing scripts (`chatfs_<provider>_<noun>_<verb>.py`, shared
`chatfs_layout.py` / `chatfs_render.py` / `chatfs_json.py`, `*.jq`, two
`.sh`). Naming design: the incubator's
`design.kb/040-design.kb/cli-command-shape.md`; shared/provider split:
its `provider-plugin-model.md`.

## Problem Statement

Scripts import siblings by flat module name, so they only run from the
incubator directory, need a scoped pyright `executionEnvironments`
workaround, and can't be packaged. Restructure into an importable `chatfs`
package *in place* (the move to `packages/` is the next child).

## Proposed Solution

Settled 2026-07-14. Shared cross-provider primitives stay at the package
root; providers nest one level under a `provider/` subpackage (ready for
the future `chatfs.providers` entry-point split, and the natural future
home for a formal base-adapter module); nouns are subpackages within each
provider, matching the CLI command path and `package-division.md`'s
`chatfs.provider.chatgpt.conversation…` example. Locator+verb join as one
leaf module filename — no separate locator directory; only 2 verbs per
locator today, an extra level buys nothing.

    chatfs/
      layout.py
      render.py
      json.py
      url_browse.py            # provider-agnostic url-browse helpers (was chatfs_url_browse.py)
      provider/
        claude/
          layout.py
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
            browse.py          # ported from .sh, see Implementation Steps
            pluck.jq
        chatgpt/  ...          # same shape, no conversation/splat.py
        aistudio/ ...          # same shape, + conversation/massage_json.py

Bare-verb leaves remain invocable (thin executable shims or `python -m`)
so the pipe surface and delegation orchestrators keep working throughout
— the driver-model decision (one importable stage function, two thin
surfaces) is the guide.

## Implementation Steps

- [ ] [Port `.jq`/`.sh` pipeline scripts to Python](2026-07-14-000-port-jq-sh-to-python.md)
      — extracted 2026-07-14 as its own tracked task (`related-effort`,
      not `blocked-by`: it runs against the current flat layout and
      doesn't need this task's package-tree decision). Ideally lands
      before or alongside the next step for whichever family it covers,
      but isn't a hard gate — do it inline here if it hasn't landed yet.
- [ ] Move one provider family end-to-end (suggest claude — has the most
      tests), tests green, as the template.
- [ ] Sweep remaining families + shared modules; delete flat scripts as
      each family lands.
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
