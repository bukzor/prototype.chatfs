---
why:
  - ../../../../docs/dev/design.kb/030-requirements.kb/atomic-cache-updates.md
  - ../../../../docs/dev/design.kb/030-requirements.kb/pipeline-composability.md
---

# Deterministic Regeneration

Every pipeline stage presumes its outputs are stale and rebuilds them
from scratch. There are no freshness caches in the user-facing scripts.

## Rule

Before a verb's outputs become visible, any prior artifact they
supersede is removed. After the verb runs, the outputs are a pure
function of the inputs and the verb's code — never a mixture of old
and new.

A verb builds its complete output in a destination-adjacent scratch
(`.tmp` sibling) and atomically promotes it over the prior artifact
(mechanism: `chatfs.shell.atomic`) -- supersession happens at the rename,
with no advance purge and no window where outputs are absent, partial,
or mixed. Failed attempts are preserved as `.fail` siblings
(latest-wins, cleared by the next success), so a crash leaves the
in-progress bytes on disk for inspection. Identity-scoped symlink
cleanup is place-then-purge: the new view symlink is placed first, then
stale ones for the same identity are swept, excluding the fresh one.

This applies to:

- `index browse` — re-runs har-browse every time; no mtime check on
  the tee'd CDP debug file.
- `conversation url browse` and `conversation path browse` —
  `capture()` stages `cdp.jsonl` and `conversation.json` into
  `.data/$UUID/` under one outer write lock; a failed browse leaves the
  prior `cdp.jsonl` untouched, a failed pluck leaves the prior
  `conversation.json` untouched.
- `index splat` — calls `place_meta` per item; `meta.json` staged into
  `.data/$UUID/`; the view symlink is placed, the prior one purged, and
  the `view` back-pointer rewritten to name the new one
  (place-then-purge).
- `conversation path render` — builds the entire derived surface
  (`chat.md`, `messages/`, the `.data` inspection symlink) in one
  staged scratch and atomically promotes it as a single swap of
  `.chat/$UUID/` (see `chat-as-directory.kb/pipeline-implications.md`).

## Identity-scoped cleanup

The cleanup above is mostly path-scoped — "rm whatever lives at the
same address we're about to write." That suffices when a verb's output
always lives at the same place.

When derivation logic puts the same identity at different paths over
time — e.g. a chat's view symlink was at the UTC ts-dir last run, lives
at a local-zone ts-dir this run — cleanup must be by identity, not by
path.

The general form: **before a verb writes its outputs, it removes any
prior artifact those outputs supersede, regardless of where the prior
artifact lived.**

For view symlinks targeting `.chat/$UUID/…`, cleanup follows a record
of the placement rather than searching for it: `place_meta` writes a
`view` back-pointer beside the chat's captured data
(`chatfs.layout.VIEW_LINK_NAME`), inside the write lock that already
covers meta.json and the symlink. Superseding a view is then a readlink
and an unlink, whatever the archive holds, and `find_view_path` reports
the live view the same way. The purge still runs *after* the fresh
symlink is placed and excludes it, so it can't undo the placement it
follows.

Searching the view trees by identity
(`chatfs.shell.place._purge_view_symlinks`) is what remains for the case
a pointer cannot cover: a chat placed before back-pointers existed. Each
such chat pays one search, on the placement that then records its
pointer. That search is also the shape a repair wants after a derivation
change, since then no pointer describes where the views *should* have
been — but that is a migration event, not a per-item one, which is the
whole reason it stopped being the default path. Measured on a replayed
1154-chat claude index: 93 s of searching per placement, 3 s of
following pointers.

This keeps the storage layer (`.chat/$UUID/`) authoritative — the only
place a UUID's view symlinks ever resolve to — while letting derived
views (`YYYY/MM/…`) heal when their derivation logic changes.

The scope of both is the labeled view trees and nothing else: they own
what they placed. A symlink to a chat that someone else left elsewhere
under the root is not a view and is not theirs to remove.

Other contexts where this applies: any pluggable view tree (by-tag,
by-model), and anywhere else identity is bound to a path that
derivation logic may relocate.

## Why not freshness caches

Stage-skipping caches hide code changes (in the stage and in external
tools it shells out to), upstream input changes, and partial-write
failures. The full rationale and history of the removal lives in
`docs/dev/adr/2026-04-29-000-no-freshness-caches.md`.
