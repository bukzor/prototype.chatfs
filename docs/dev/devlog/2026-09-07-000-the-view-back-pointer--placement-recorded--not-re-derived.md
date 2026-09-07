# 2026-09-07 The view back-pointer: placement recorded, not re-derived

## Focus

Close the last item of the quadratic-splat thread: stop searching the view
trees for a chat's current view symlink, since the placement already knew
where it was.

## What happened

`place_meta` writes `.data/$UUID/view`, a relative symlink naming the view
symlink it just placed, inside the write lock that already covers meta.json
and the symlink itself. The next placement follows it -- one readlink, one
unlink -- instead of walking every view looking for a symlink whose target
mentions the uuid. `find_view_path` (which every render calls) reads the
same pointer.

Three cases, and each pays what it owes:

- **carrying a pointer** -- readlink. The common case, forever after.
- **never placed here** -- nothing. No meta.json means nothing has ever
  derived a view path for this chat, so there is no prior view to purge.
  Without this, a fresh cache would pay a search per chat on its first
  index, which is exactly the archive-scaled cost being removed.
- **placed before back-pointers existed** -- one search, on the placement
  that then records a pointer. That is the migration, and it needs no
  command: the next ordinary splat performs it.

### Measured

Replayed 1154-chat claude index (1254 placements, the extra 100 being
duplicate-uuid re-writes across index pages):

| | wall |
|---|---|
| search per placement (yesterday's narrowed walk) | 93 s |
| migration run: search once, record | 97 s |
| steady state: follow the pointer | 3 s |

The resulting view tree is byte-identical to the one the search produces:
1154 chats, 1154 pointers, 1154 symlinks, no duplicate targets.

### Why not delete the search

Asked directly, having seen `VIEW_TREE_GLOB` land yesterday: with a pointer,
can the glob go? No. Two callers still need to name the view trees, and
neither has a pointer to follow -- the legacy chat above, and any repair
after a derivation change, which is precisely the case where no pointer
describes where the views *should* have been. Even the most aggressive
repair (`rm -rf` the view trees, re-place from meta.json) has to name them.
What the glob lost is the hot path, not its reason to exist.

### On the tests

Two of the new assertions passed on first run -- `find_view_path` returning
None for a never-placed chat, and for one whose view a human deleted. Both
were driven red by mutation instead: dropping the staleness check returns a
path that no longer exists, and dropping the absent-pointer guard raises
`FileNotFoundError` from `readlink`. A guard nobody has watched fail is a
guard nobody knows is wired up.

## Left standing

A crash in the syscall-width window between purging the prior view and
recording the new pointer leaves the pointer naming a path that is gone.
The next placement unlinks nothing (`missing_ok`) and re-records, so the
state self-heals unless a *third* placement lands in between -- which
would orphan the middle symlink. Same class as the place-then-purge window
already documented in `deterministic-regeneration.md`, and the
identity-scoped search is still the repair for it.
