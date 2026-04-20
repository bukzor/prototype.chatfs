# FUSE Mount

A userspace FUSE daemon presents the cache as a real filesystem. Reads
(`readdir`, `getattr`, `open`, `read`) serve from local cache content; the
daemon has no network client in the read path.

Standard tools (`ls`, `cat`, `grep`, `find`, editors, file managers) work
unmodified. Sync happens outside the read path via a separate control plane
(see `../sync-control-plane.md`).

**Pros.** Every OS-level tool that opens files becomes a chatfs client for
free. Structural enforcement of the no-network-on-read requirement: the read
code path doesn't have access to a network client. Mount lifetime is tied to
the daemon process — no ports, no auth, no listener.

**Cons.** Requires a running daemon. Userspace FUSE imposes a per-syscall
overhead (ns-to-µs) — real but negligible next to disk and human latencies.
Cross-platform support is Linux-first; macOS works via macFUSE, Windows via
WinFsp with caveats.

**Background.** See `../../../background.kb/fuse-filesystem.md` and the
Google Piper precedent referenced from `020-goals.kb/lazy-filesystem.md`.
