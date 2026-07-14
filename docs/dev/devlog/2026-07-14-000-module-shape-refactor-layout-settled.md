# Devlog: 2026-07-14 — module-shape-refactor layout settled

## Focus

Session start picked up the 2026-07-13 graduation-and-integration umbrella
(`.claude/todo.kb/2026-07-13-000-graduation-and-integration.md`). Two
children were unblocked (`000-module-shape-refactor`,
`002-path-ownership-contract-v1`) plus the incubator's atomic-regeneration
todo; two other agents took 002 and atomic-regeneration concurrently in
the same working directory, this session focused on 000: settling the
target module-tree shape before any code moves, per the user's request to
agree on shape before diving deep.

## Decisions

### Module tree shape for the `chatfs` package

**Settled layout:**

    chatfs/
      layout.py
      render.py
      json.py
      url_browse.py            # provider-agnostic url-browse helpers
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
            browse.{sh,py}     # .sh-vs-.py still open
            pluck.jq
        chatgpt/  ...          # same shape, no conversation/splat.py
        aistudio/ ...          # same shape, + conversation/massage_json.py

**Rationale:**
- Nouns-as-subpackages (not flat `noun_verb.py` modules) was already
  decided one layer up: `package-division.md` justifies the bare `chatfs`
  import name with the path `chatfs.chatgpt.conversation…`, so the
  incubator todo's "Open Questions" bullet asking this was stale, not
  actually open.
- The flat `chatfs_<provider>_<noun>_<locator>_<verb>.py` names are a
  deliberate flattened encoding of the CLI subcommand path — confirmed by
  `cli-command-shape.md`: "Python module names use `_` for the same path"
  as the kebab `$PATH` commands. The refactor un-flattens; it doesn't
  redesign.
- Locator+verb stay joined as one leaf filename (`url_browse.py`, not
  `url/browse.py`) — only 2 verbs per locator today, an extra directory
  level buys nothing.
- Shared cross-provider primitives (`layout.py`, `render.py`, `json.py`,
  `url_browse.py`) stay at the package root, named for what they hold —
  no hedge words. `json.py` drops the `_util` suffix floated earlier
  (rejected: "util" is a five-dollar word for "misc"); Python 3's
  absolute-import default means no real stdlib-shadowing risk.
  `url_browse.py` keeps its name as the designated home for whatever's
  shared at the `url`×`browse` intersection (today: `null_tolerant_
  mismatches`), matching `layout.py`/`render.py`'s pattern — a module
  named for its role, not narrowed to today's one function.
- Providers nest one level under `chatfs/provider/`, not directly under
  `chatfs/`. Motivation: keeps the root namespace as "shared library +
  provider registry," mirrors the future `chatfs.providers` entry-point
  group name (`package-division.md`'s extension-point-naming section),
  and gives a natural home for a future formal base-adapter module
  without crowding the root.

**Alternatives considered:** flat `noun_verb.py` modules directly under
each provider (rejected — loses the noun-as-command-path-segment fidelity
that `package-division.md` already committed to); providers directly
under `chatfs/` with no `provider/` grouping (rejected this session —
user wanted the extra level for the entry-point-group symmetry).

### Follow-up doc fix

`package-division.md`'s own example path (`chatfs.chatgpt.conversation…`)
was stale the moment `provider/` was added — patched in place to
`chatfs.provider.chatgpt.conversation…` rather than deferred to child 005's
reconciliation pass, since it's a one-line fix in a required-reading doc.

## Conventions Established

- When a design doc's illustrative example (a literal dotted path, a
  filename) is superseded by a later decision, patch it immediately if
  the fix is small and the doc is required-reading elsewhere — don't let
  a stale example outlive the decision that invalidated it, even if a
  later reconciliation pass would eventually catch it.

## Open Questions

- Where `.jq` filters live as package data (`importlib.resources`) and
  whether the two `.sh` index-browse scripts convert to Python — deferred
  to 000's Implementation Steps, not shape-critical.
- Bare-verb leaf invocation mechanics (thin executable shims vs
  `python -m chatfs.provider.<x>.<y>.<verb>`) — orthogonal to the tree
  shape, unresolved.

## References

- `.claude/todo.kb/2026-07-13-000-graduation-and-integration.kb/2026-07-13-000-module-shape-refactor.md`
  — the child task, updated in place with this settled layout.
- `docs/dev/design.kb/040-design.kb/package-division.md` — parent design
  doc, patched.
- `docs/dev/design-incubators/chatfs-cli-mockup/design.kb/040-design.kb/cli-command-shape.md`
  and its `cli-command-shape.kb/` — CLI noun/verb/locator vocabulary this
  layout mirrors.
