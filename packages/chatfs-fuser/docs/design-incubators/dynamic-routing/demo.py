"""Sketch: lazy inode ↔ path mapping for dynamic FUSE directories.

Design assumptions:
- entry_valid = 0 (attr_valid = 0): the kernel re-validates on every access.
  This is appropriate for a highly dynamic filesystem (like /proc). It means
  the kernel never serves stale dentries — every lookup/getattr/readdir hits
  the FUSE daemon, which re-evaluates user callbacks for fresh data.
- Callbacks are re-evaluated on every access (stateless path resolution).
  _resolve_entry() re-walks from root each time, calling read() at each Dir
  level. This is a feature: it guarantees fresh data (or fresh errors) rather
  than serving stale cached entries. The cost of re-evaluation is the caller's
  to manage — if read() is expensive, the caller should cache it.
- Races between readdir and subsequent access are expected and normal. A
  readdir may return entries that are gone by the time the caller accesses
  them. This is standard dynamic filesystem behavior (same as /proc, or any
  ext4 directory with concurrent deletes). The framework handles it correctly:
  _resolve_entry() raises ENOENT, same as any POSIX filesystem.
- Inode table is append-only. Stale inodes for vanished entries return ESTALE
  on access (the framework detects: inode exists in table but resolution raised
  ENOENT → stale handle). No inode GC or generation numbers at current scale.
- Caching is the caller's responsibility. The VFS framework is intentionally
  stateless w.r.t. data freshness — it lacks the information to determine
  cache validity, and the user's callbacks can cache as they see fit.
- All errors are filesystem errors (FuseError with errno), never Python
  exceptions.

Key design decision — unified PathSegment:
  Three variants, all callback-driven. No static/dynamic split.
  - Dir:     read() -> dict[str, PathSegment]
  - File:    read() -> str
  - Symlink: read() -> str
  A "static" dir is just one whose read() returns a fixed dict. The framework
  doesn't distinguish — same resolution path, same inode lifecycle.

Future work (if needed):
- Push invalidation: notify_inval_entry(parent, name) for nonzero timeouts.
- Parameter threading: routing-style framework to thread parent path segments.
- Inode reaping: on FUSE forget(ino), remove from tables.

Design rules:
1. Stateless re-evaluation. Every access re-walks from root. No framework
   caching. Caching is the caller's problem.
2. POSIX error semantics. All errors are filesystem errnos. ENOENT for missing,
   ESTALE for stale handles, ENOTDIR/EISDIR for type mismatches.
3. Append-only inodes. Table grows monotonically. Stale → ESTALE.
"""

from __future__ import annotations

import errno
from dataclasses import dataclass, field
from collections.abc import Callable


class FuseError(OSError):
    """Filesystem error with an errno, translated to FUSE error replies."""
    def __init__(self, err: int, msg: str = ""):
        super().__init__(err, msg)


# -- PathSegment: the user-defined tree --

@dataclass
class Dir:
    """Directory. read() returns children on each access."""
    read: Callable[[], dict[str, PathSegment]]

@dataclass
class File:
    """File. read() returns content on each access."""
    read: Callable[[], str]

@dataclass
class Symlink:
    """Symlink. read() returns target on each access."""
    read: Callable[[], str]

PathSegment = Dir | File | Symlink


# -- The FUSE kernel's view: everything is inodes --

@dataclass
class FuseRequest:
    """Simulates what FUSE sends us."""
    def readdir(self, fs: VFS, ino: int) -> list[tuple[int, str]]:
        return fs.do_readdir(ino)

    def lookup(self, fs: VFS, parent_ino: int, name: str) -> int:
        return fs.do_lookup(parent_ino, name)

    def read(self, fs: VFS, ino: int) -> str:
        return fs.do_read(ino)


# -- The library's internals: inode ↔ path translation --

@dataclass
class VFS:
    """The library's internal layer: translates inodes ↔ paths."""
    root: PathSegment  # typically a Dir
    ino_to_path: dict[int, str] = field(default_factory=dict)
    path_to_ino: dict[str, int] = field(default_factory=dict)
    next_ino: int = 2  # 1 = root

    def __post_init__(self):
        self.ino_to_path[1] = "/"
        self.path_to_ino["/"] = 1

    def _ensure_ino(self, path: str) -> int:
        if path in self.path_to_ino:
            return self.path_to_ino[path]
        ino = self.next_ino
        self.next_ino += 1
        self.ino_to_path[ino] = path
        self.path_to_ino[path] = ino
        return ino

    def _resolve_entry(self, path: str) -> PathSegment:
        """Walk path segments through the entry tree.

        Returns self.root for "/". Raises FuseError(ENOENT) if any segment
        is missing — the normal case when backing data changes between
        readdir and access (standard filesystem race, same as any dynamic fs).
        """
        parts = [p for p in path.strip("/").split("/") if p]
        node = self.root
        for part in parts:
            if not isinstance(node, Dir):
                raise FuseError(errno.ENOTDIR, path)
            children = node.read()
            try:
                node = children[part]
            except KeyError:
                raise FuseError(errno.ENOENT, path) from None
        return node

    def do_readdir(self, ino: int) -> list[tuple[int, str]]:
        path = self.ino_to_path.get(ino)
        if path is None:
            raise FuseError(errno.ENOENT, str(ino))
        entry = self._resolve_entry(path)

        if not isinstance(entry, Dir):
            raise FuseError(errno.ENOTDIR, path)

        children = entry.read()
        result = []
        for name in children:
            child_path = f"{path.rstrip('/')}/{name}"
            child_ino = self._ensure_ino(child_path)
            result.append((child_ino, name))
        return result

    def do_lookup(self, parent_ino: int, name: str) -> int:
        parent_path = self.ino_to_path.get(parent_ino)
        if parent_path is None:
            raise FuseError(errno.ENOENT, str(parent_ino))
        child_path = f"{parent_path.rstrip('/')}/{name}"
        return self._ensure_ino(child_path)

    def do_read(self, ino: int) -> str:
        path = self.ino_to_path.get(ino)
        if path is None:
            raise FuseError(errno.ENOENT, str(ino))
        try:
            entry = self._resolve_entry(path)
        except FuseError as e:
            if e.errno == errno.ENOENT:
                # Inode exists in table but path no longer resolves → stale
                raise FuseError(errno.ESTALE, path) from None
            raise
        if isinstance(entry, Dir):
            raise FuseError(errno.EISDIR, path)
        if isinstance(entry, Symlink):
            return entry.read()
        return entry.read()


# -- The user's view: everything is paths and callbacks --


class UserVFSModule:
    """User's business logic — no framework types, no inodes, just data."""

    # Data sources (in real life: API calls, cache reads, etc.)
    convos_by_org = {
        "personal": ["conv-aaa", "conv-bbb"],
        "work": ["conv-ccc"],
    }
    messages_by_convo = {
        "conv-aaa": "Hello world",
        "conv-bbb": "Goodbye world",
        "conv-ccc": "Work stuff",
    }

    @staticmethod
    def list_orgs() -> list[str]:
        return list(UserVFSModule.convos_by_org.keys())

    @staticmethod
    def list_convos(org: str) -> list[str]:
        return UserVFSModule.convos_by_org[org]

    @staticmethod
    def read_convo(convo: str) -> str:
        return UserVFSModule.messages_by_convo[convo]

    @staticmethod
    def readme() -> str:
        return "# chatfs\n"

    @staticmethod
    def construct_vfs() -> VFS:
        """Wire business logic into framework — this is the seam.

        Note how the "dynamic" orgs directory and "static" root directory
        use the same Dir type — they just return different dicts.
        """
        root = Dir(read=lambda: {
            "README.md": File(read=UserVFSModule.readme),
            "orgs": Dir(read=lambda: {
                org: Dir(read=lambda org=org: {
                    convo: File(read=lambda convo=convo: UserVFSModule.read_convo(convo))
                    for convo in UserVFSModule.list_convos(org)
                })
                for org in UserVFSModule.list_orgs()
            }),
        })
        return VFS(root=root)


def main():
    fs = UserVFSModule.construct_vfs()
    fuse = FuseRequest()

    # ls /
    print("ls /")
    for ino, name in fuse.readdir(fs, 1):
        print(f"  {name} (ino={ino})")

    # ls /orgs
    orgs_ino = fuse.lookup(fs, 1, "orgs")
    print(f"\nls /orgs (ino={orgs_ino})")
    for ino, name in fuse.readdir(fs, orgs_ino):
        print(f"  {name} (ino={ino})")

    # ls /orgs/personal
    personal_ino = fuse.lookup(fs, orgs_ino, "personal")
    print(f"\nls /orgs/personal (ino={personal_ino})")
    for ino, name in fuse.readdir(fs, personal_ino):
        print(f"  {name} (ino={ino})")

    # cat /orgs/personal/conv-aaa
    conv_ino = fuse.lookup(fs, personal_ino, "conv-aaa")
    print(f"\ncat /orgs/personal/conv-aaa (ino={conv_ino})")
    print(f"  {fuse.read(fs, conv_ino)!r}")

    # cat /README.md
    readme_ino = fuse.lookup(fs, 1, "README.md")
    print(f"\ncat /README.md (ino={readme_ino})")
    print(f"  {fuse.read(fs, readme_ino)!r}")

    # Show the inode table
    print(f"\nInode table ({len(fs.ino_to_path)} entries):")
    for ino, path in sorted(fs.ino_to_path.items()):
        print(f"  {ino}: {path}")


if __name__ == "__main__":
    main()
