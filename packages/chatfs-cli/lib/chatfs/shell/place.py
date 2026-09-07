"""Place: the fs half of storage/view-tree maintenance -- meta.json,
the view dir-symlink, and the `.chat`/`.data` resolution helpers built
on top of `chatfs.layout`'s pure vocabulary.

Exception to chatfs/'s purity rule (see chatfs.shell's package docstring):
every function here does real I/O.
"""

import json
import os
from collections.abc import Iterator, Mapping
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

from chatfs.layout import (
    DATA_DIR_NAME,
    VIEW_LINK_NAME,
    VIEW_TREE_GLOB,
    chat_dir_for,
    data_dir_for,
    safe_filename,
    time_dir_for,
)
from chatfs.shell import atomic as chatfs_atomic
from chatfs.shell import locks as chatfs_locks


def link_data_dir(dst: Path, uuid: str) -> None:
    """Create/refresh `dst/.data` as a symlink to `.data/$UUID`.

    Absolute target, not relative: a relative `../../.data/$UUID`
    dangles the moment `dst` is `cp -ar`'d anywhere else, since the copy
    keeps the same two-levels-up text but no longer sits under `root`.
    An absolute target survives the copy -- it still resolves, back to
    this same cache's `.data/$UUID` -- so `cp -ar`ing a chat dir out of
    the cache doesn't leave its `.data` inspection link broken.

    Same target either way `dst` is passed: the final chat_dir
    (`root/.chat/$UUID/`) or a same-depth staged scratch sibling
    (`root/.chat/.{$UUID}.tmp/`) -- both sit two levels below `root`.
    `uuid` is taken explicitly rather than `dst.name`, since that
    assumption breaks for the scratch case.
    """
    link = dst / DATA_DIR_NAME
    if link.is_symlink() or link.exists():
        link.unlink()
    link.symlink_to((dst.parent.parent / DATA_DIR_NAME / uuid).resolve())


def resolve_chat_dir(arg: str | os.PathLike[str]) -> Path:
    """Resolve any path-into-or-pointing-at a `.chat/$UUID/` to that dir.

    Handles: the chat dir itself, files or subdirs inside it, its
    `.data` inspection symlink (and paths descending through it into
    the real `.data/$UUID/` tree), a `.data/$UUID/` path reached
    directly, view dir-symlinks, and paths descending through view
    dir-symlinks (e.g. `view/$TITLE/.data/foo`) -- climbing by
    `p.parent.name` rather than `is_dir()`, so a not-yet-rendered
    (nonexistent) chat_dir or a dangling view symlink resolves
    correctly instead of requiring existence.

    Does not assert the result exists: `.chat/$UUID/` legitimately
    doesn't, before first render (see chatfs.layout's module docstring).
    Callers that need captured state present check for it explicitly
    (e.g. via `chatfs.layout.data_dir_of`).
    """
    p = Path(arg).resolve()
    while True:
        if p.parent.name == ".chat":
            return p
        if p.parent.name == ".data":
            return chat_dir_for(p.name, p.parent.parent)
        assert p.parent != p, f"reached fs root without finding .chat or .data: {arg}"
        p = p.parent


def _view_symlinks(uuid: str, root: Path) -> Iterator[Path]:
    """Yield every view-tree symlink under `root` whose target mentions
    `uuid`.

    The search of last resort: it costs a walk of every view placed, so
    callers reach it only for a chat carrying no back-pointer
    (`chatfs.layout.VIEW_LINK_NAME`), which they then record.

    Walks the labeled view trees only (`chatfs.layout.VIEW_TREE_GLOB`),
    which excludes three subtrees by construction rather than by
    filtering after the fact. `.chat/` and `.data/` hold
    storage-internal symlinks (e.g. `.chat/$UUID/.data`'s inspection
    link back to `.data/$UUID/`), not views, and their targets
    legitimately contain the uuid too. `trash/` holds a preserved
    artifact, not a view: a re-captured chat must not reach into an
    earlier trashing of itself.
    """
    for tree in root.glob(VIEW_TREE_GLOB):
        for path in tree.rglob("*"):
            if path.is_symlink() and uuid in os.readlink(path):
                yield path


def _purge_view_symlinks(uuid: str, root: Path, *, keep: Path | None = None) -> None:
    """Remove every view-tree symlink under `root` whose target mentions
    `uuid`, except `keep`.

    Identity-scoped cleanup by search, for the chat whose back-pointer
    can't say where its view is. Also the shape a repair after a
    derivation change wants, since then no pointer describes where the
    views should have been.

    `keep` is the symlink `place_meta` just placed (place-then-purge:
    see `deterministic-regeneration.md`) -- its target also contains
    `uuid`, so without this exclusion the sweep would immediately
    undo the placement it's meant to follow.
    """
    for path in _view_symlinks(uuid, root):
        if path != keep:
            path.unlink()


def _recorded_view(data_dir: Path) -> Path | None:
    """The view symlink `place_meta` recorded for this chat, or None when
    it recorded none: a chat this cache has never placed, or one placed
    before back-pointers existed.

    The recorded target is relative, so joining it back onto `data_dir`
    -- without resolving the last component -- recovers the view symlink
    itself rather than the chat dir it in turn points at.
    """
    link = data_dir / VIEW_LINK_NAME
    if not link.is_symlink():
        return None
    return Path(os.path.normpath(data_dir / os.readlink(link)))


def _purge_prior_view(uuid: str, root: Path, *, keep: Path, placed_before: bool) -> None:
    """Remove the view symlink this chat had before `keep` was placed.

    One readlink for a chat carrying a back-pointer, whatever the
    archive's size, and nothing at all for a chat this cache has never
    placed (`placed_before`, i.e. no meta.json yet: nothing has ever
    derived a view path for it). Only a chat placed before back-pointers
    existed pays the search -- and `place_meta` records a pointer on its
    way out, so a cache pays that once per chat, ever.
    """
    prior = _recorded_view(data_dir_for(uuid, root))
    if prior is not None:
        if prior != keep:
            prior.unlink(missing_ok=True)
    elif placed_before:
        _purge_view_symlinks(uuid, root, keep=keep)


def find_view_path(uuid: str, root: Path) -> Path | None:
    """The view-tree symlink under `root` naming `uuid`'s chat -- the
    "nice" (title, not UUID) path a human navigates to, for callers that
    want to report it (e.g. printing where a rendered chat.md landed).

    None when no view is placed: never placed, or placed and since
    deleted -- `place_meta` keeps at most one live view symlink per
    uuid, so a recorded pointer that no longer names a symlink means
    there is nothing left to report.

    Falls back to searching for a chat placed before back-pointers
    existed; the next `place_meta` records one and ends that.
    """
    recorded = _recorded_view(data_dir_for(uuid, root))
    if recorded is not None:
        return recorded if recorded.is_symlink() else None
    return next(_view_symlinks(uuid, root), None)


class Placement(NamedTuple):
    """One chat as `place_meta` left it: the identity it was placed
    under, its storage dir, and the live view symlink into that dir.

    `record()` is the shape index splat writes to stdout, one line per
    chat placed. Identity comes from here rather than from a provider's
    own index item so the stream reads the same whichever provider
    produced it -- `id`/`title` are already the normalized fields every
    provider's leaf extracts before calling place_meta.

    `updated` is the provider's own last-changed timestamp, normalized
    across providers. It rides the record because meta.json is the only
    other place it exists and the splat overwrites that file before any
    consumer reads it -- so a consumer deciding whether a chat is worth
    re-capturing can only learn the previous answer from here. None when
    the provider's index doesn't say.
    """

    id: str
    title: str
    chat_dir: Path
    view: Path
    updated: datetime | None

    def record(self) -> dict[str, str | None]:
        """The JSONL line: every key always present, `updated` null when
        unknown, so consumers filter one fixed shape."""
        return {
            "id": self.id,
            "title": self.title,
            "chat_dir": str(self.chat_dir),
            "view": str(self.view),
            "updated": self.updated.isoformat() if self.updated else None,
        }


def place_meta(
    id: str,
    title: str,
    created: datetime,
    item: Mapping[str, object],
    root: Path,
    *,
    label: str = "Created",
    updated: datetime | None = None,
) -> Placement:
    """Write meta.json into `.data/$UUID/`, refresh the view dir-symlink.

    `item` is serialized verbatim into meta.json (the provider's full
    index entry, pass-through fields included); `id`/`title`/`created`
    are the already-extracted identity fields a provider's leaf entry
    point pulls out of it. Falls back to `id` when `title` is empty,
    so an empty-titled chat never collapses its view symlink onto
    `view_dir` itself.

    `updated` is reported back in the `Placement` only -- it reaches
    meta.json (if at all) as one of `item`'s own fields, and never
    affects the view tree or the label.

    `label` forwards to `time_dir_for` — see there. Storage placement
    (`.data/$UUID/`) and the identity-scoped symlink purge are
    unaffected by it: only the derived view-tree segment changes, so a
    later `place_meta` call with real creation time (different `label`)
    still finds and replaces this call's symlink by uuid, moving the
    chat from the labeled tree to the true date tree.

    Both meta.json and the view symlink are staged-and-promoted, and
    the stale-symlink purge runs only after the fresh one is placed
    (place-then-purge, not purge-then-place: see
    `deterministic-regeneration.md`) -- a crash never makes the chat
    vanish from every view. The purge follows the back-pointer this
    call then rewrites (`chatfs.layout.VIEW_LINK_NAME`), so replacing a
    view costs a readlink rather than a search. All four updates share
    one outer write lock on the data dir, so a cooperating reader sees
    them as a single transition.

    Does not touch `.chat/$UUID/` -- it may not exist yet (see
    chatfs.layout's module docstring); that's render's job. The
    returned `Placement`'s chat_dir is therefore possibly
    not-yet-existing, for callers that pass it on to render.
    """
    chat_dir = chat_dir_for(id, root)
    data_dir = data_dir_for(id, root)
    data_dir.mkdir(parents=True, exist_ok=True)
    meta_path = data_dir / "meta.json"

    view_dir = root / time_dir_for(created, label=label)
    view_dir.mkdir(parents=True, exist_ok=True)
    title_link = view_dir / safe_filename(title or id)

    with chatfs_locks.write_locked(data_dir):
        placed_before = meta_path.exists()  # before the write below makes it so

        with chatfs_atomic.staged(meta_path, anchor=data_dir) as tmp:
            _ = tmp.write_text(json.dumps(item, indent=2) + "\n")

        with chatfs_atomic.staged(title_link, anchor=data_dir) as tmp:
            tmp.symlink_to(os.path.relpath(chat_dir, start=view_dir))

        _purge_prior_view(id, root, keep=title_link, placed_before=placed_before)

        with chatfs_atomic.staged(data_dir / VIEW_LINK_NAME, anchor=data_dir) as tmp:
            tmp.symlink_to(os.path.relpath(title_link, start=data_dir))

    return Placement(id, title, chat_dir, title_link, updated)
