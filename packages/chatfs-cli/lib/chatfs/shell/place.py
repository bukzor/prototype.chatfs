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

    Skips `.chat/` and `.data/` -- those hold storage-internal symlinks
    (e.g. `.chat/$UUID/.data`'s inspection link back to `.data/$UUID/`),
    not views, and their targets legitimately contain the uuid too.
    Skips `trash/` -- trashed content is a preserved artifact, not a
    view (a re-captured chat must not reach into an earlier trashing of
    itself).
    """
    for path in root.rglob("*"):
        rel_parts = path.relative_to(root).parts
        if ".chat" in rel_parts or ".data" in rel_parts or "trash" in rel_parts:
            continue
        if path.is_symlink() and uuid in os.readlink(path):
            yield path


def _purge_view_symlinks(uuid: str, root: Path, *, keep: Path | None = None) -> None:
    """Remove every view-tree symlink under `root` whose target mentions
    `uuid`, except `keep`.

    Identity-scoped cleanup: derived view paths can move when
    derivation logic changes (TZ format, view shape); we sweep by
    identity, not path.

    `keep` is the symlink `place_meta` just placed (place-then-purge:
    see `deterministic-regeneration.md`) -- its target also contains
    `uuid`, so without this exclusion the sweep would immediately
    undo the placement it's meant to follow.
    """
    for path in _view_symlinks(uuid, root):
        if path != keep:
            path.unlink()


def find_view_path(uuid: str, root: Path) -> Path | None:
    """The view-tree symlink under `root` naming `uuid`'s chat -- the
    "nice" (title, not UUID) path a human navigates to, for callers that
    want to report it (e.g. printing where a rendered chat.md landed).

    None if no view has been placed yet. `place_meta`'s place-then-purge
    protocol keeps at most one live view symlink per uuid at a time, so
    the first match is the only one there is to find.
    """
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
    vanish from every view. All three updates share one outer write
    lock on the data dir, so a cooperating reader sees them as a single
    transition.

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
        with chatfs_atomic.staged(meta_path, anchor=data_dir) as tmp:
            _ = tmp.write_text(json.dumps(item, indent=2) + "\n")

        with chatfs_atomic.staged(title_link, anchor=data_dir) as tmp:
            tmp.symlink_to(os.path.relpath(chat_dir, start=view_dir))

        _purge_view_symlinks(id, root, keep=title_link)

    return Placement(id, title, chat_dir, title_link, updated)
