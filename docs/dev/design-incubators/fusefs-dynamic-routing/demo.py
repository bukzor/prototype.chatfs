"""Sketch: lazy inode ↔ path mapping for dynamic FUSE directories.

Design assumptions:
- entry_valid = 0 (attr_valid = 0): the kernel re-validates on every access.
  This is appropriate for a highly dynamic filesystem (like /proc). It means
  the kernel never serves stale dentries — every lookup/getattr/readdir hits
  the FUSE daemon, which re-evaluates user callbacks for fresh data.
  (entry_valid is a FUSE protocol concept: the duration the kernel trusts a
  cached dentry before re-lookup. Set by the daemon in lookup replies.)
- Callbacks are re-evaluated on every access (stateless path resolution).
  _resolve_entry() re-walks from root each time, calling list()+template() at
  each level. This is a feature: it guarantees fresh data (or fresh errors)
  rather than serving stale cached entries. The cost of re-evaluation is the
  caller's to manage — if list() is expensive, the caller should cache it.
- Races between readdir and subsequent access are expected and normal. A
  readdir may return entries that are gone by the time the caller accesses
  them. This is standard dynamic filesystem behavior (same as /proc, or any
  ext4 directory with concurrent deletes). The framework handles it correctly:
  _resolve_entry() raises ENOENT, same as any POSIX filesystem. The framework
  does not introduce races beyond what any dynamic filesystem has.
- Inode table is append-only. Stale inodes for vanished entries return ESTALE
  on access (the framework detects: inode exists in table but resolution raised
  ENOENT → stale handle). ESTALE is the POSIX errno for this situation (cf.
  NFS stale file handles). No inode GC or generation numbers at current scale.
- Caching is the caller's responsibility. The VFS framework is intentionally
  stateless w.r.t. data freshness — it lacks the information to determine
  cache validity, and the user's callbacks can cache as they see fit.
- All errors are filesystem errors (FuseError with errno), never Python
  exceptions. KeyError → ENOENT (or ESTALE if inode exists), traversal
  through a file → ENOTDIR, read on a directory → EISDIR.

Future work (if needed):
- Push invalidation: let user code signal "entity X changed", have the VFS call
  notify_inval_entry(parent, name) on the kernel. Without this, freshness is
  entirely re-evaluation-driven (fine with entry_valid=0, but push would allow
  nonzero timeouts for better performance without staleness).
- Parameter threading: the template(name)->Entry pattern requires user closures
  for partial application. A routing-style framework (cf. FastAPI Depends, Axum
  extractors) could thread parent path segments automatically. See
  CLAUDE.md "Open design question" and "Prior art" sections.
- Inode reaping: on FUSE forget(ino) (kernel drops all references), remove the
  entry from ino_to_path/path_to_ino. Turns append-only into append-and-reap.
  No GC sweep, no generations — driven entirely by kernel lifecycle signals.

Design rules (distilled from the above):
1. Stateless re-evaluation. Every access re-walks from root, re-calling user
   callbacks. No framework-level caching. entry_valid=0 extends this to the
   kernel. Caching is the caller's problem. Consequence: fresh data or fresh
   errors on every access; races are standard POSIX behavior, not a framework
   deficiency; data that "comes back" is self-healing.
2. POSIX error semantics. All errors are filesystem errnos, never Python
   exceptions. ENOENT for missing entries, ESTALE for stale inode handles
   (inode exists in table but resolution fails), ENOTDIR/EISDIR for type
   mismatches.
3. Append-only inodes. Inode table grows monotonically. Stale inodes get
   ESTALE on access. Future: reap on forget() (kernel-driven, no GC).
"""

from __future__ import annotations

import errno
from dataclasses import dataclass, field
from collections.abc import Callable


class FuseError(OSError):
    """Filesystem error with an errno, translated to FUSE error replies."""
    def __init__(self, err: int, msg: str = ""):
        super().__init__(err, msg)


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
    root: Entry  # typically a StaticDir
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

    def _resolve_entry(self, path: str) -> Entry:
        """Walk path segments through the entry tree.

        Returns self.root for "/". Raises FuseError(ENOENT) if any segment
        is missing — the normal case when backing data changes between
        readdir and access (standard filesystem race, same as any dynamic fs).
        """
        parts = [p for p in path.strip("/").split("/") if p]
        node = self.root
        for part in parts:
            # get children of current node
            if isinstance(node, StaticDir):
                entries = node.children
            elif isinstance(node, DynamicDir):
                entries = {name: node.template(name) for name in node.list()}
            else:
                raise FuseError(errno.ENOTDIR, path)
            try:
                node = entries[part]
            except KeyError:
                raise FuseError(errno.ENOENT, path) from None
        return node

    def do_readdir(self, ino: int) -> list[tuple[int, str]]:
        path = self.ino_to_path[ino]
        entry = self._resolve_entry(path)

        if isinstance(entry, StaticDir):
            names = list(entry.children.keys())
        elif isinstance(entry, DynamicDir):
            names = entry.list()
        else:
            raise FuseError(errno.ENOTDIR, path)

        result = []
        for name in names:
            child_path = f"{path.rstrip('/')}/{name}"
            child_ino = self._ensure_ino(child_path)
            result.append((child_ino, name))
        return result

    def do_lookup(self, parent_ino: int, name: str) -> int:
        parent_path = self.ino_to_path[parent_ino]
        child_path = f"{parent_path.rstrip('/')}/{name}"
        return self._ensure_ino(child_path)

    def do_read(self, ino: int) -> str:
        path = self.ino_to_path[ino]
        entry = self._resolve_entry(path)
        if not isinstance(entry, File):
            raise FuseError(errno.EISDIR, path)
        return entry.read()


# -- User-defined tree entries --

@dataclass
class File:
    read: Callable[[], str]

@dataclass
class StaticDir:
    children: dict[str, Entry]

@dataclass
class DynamicDir:
    list: Callable[[], list[str]]
    template: Callable[[str], Entry]

Entry = File | StaticDir | DynamicDir


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
    def convo_template(convo: str) -> Entry:
        return File(read=lambda: UserVFSModule.read_convo(convo))

    @staticmethod
    def org_template(org: str) -> Entry:
        return DynamicDir(
            list=lambda: UserVFSModule.list_convos(org),
            template=UserVFSModule.convo_template,
        )

    @staticmethod
    def construct_vfs() -> VFS:
        """Wire business logic into framework — this is the seam."""
        root = StaticDir(children={
            "README.md": File(read=UserVFSModule.readme),
            "orgs": DynamicDir(
                list=UserVFSModule.list_orgs,
                template=UserVFSModule.org_template,
            ),
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
