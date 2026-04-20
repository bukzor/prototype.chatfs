# Network Mount Protocols (WebDAV, NFS, SMB)

A server process serves the cache over a network filesystem protocol. Users
mount it locally using standard OS tools (`mount -t nfs`, `mount -t davfs`,
etc.).

**Pros.** Same standard-tools win as FUSE. Well-understood protocols, broad
OS support. Decouples the server (could run remotely, shared across machines)
from the mount.

**Cons.** Requires a network stack, a listening port, authentication, and
typically a server process that outlives a single user session. Cross-machine
semantics (locking, caching, offline behavior) are protocol-dependent and
often surprising. Overkill for a per-user local cache.

FUSE runs in-process with no exposed port; WebDAV/NFS would introduce a
significantly larger surface area (auth, ACLs, network reachability) for no
additional user-visible capability in the single-user case.
