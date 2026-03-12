# Google Piper Precedent

Google's monorepo (Piper/google3) uses FUSE-based workspace mounts that are
architecturally analogous to chatfs:

```
editor / shell
       ↓
FUSE mount (google3 workspace)  ←→  macFUSE on macOS
       ↓
workspace client + local cache
       ↓
Piper backend service
```

**Key properties matching chatfs design:**
1. FUSE user-space filesystem
2. Local metadata/cache layer
3. Remote fetch only when needed (lazy)
4. Background worker processes for expensive operations
5. Reads from cache unless missing/invalidated
6. Expensive operations outside the filesystem call path

**Lesson:** The filesystem layer is kept very thin — FUSE only reads cached
data; cache misses trigger background jobs. This pattern works at enormous
scale (entire Google monorepo). Validates the "no work on read" invariant.

On macOS, Google uses macFUSE (formerly OSXFUSE) — the same kernel extension
available for chatfs.
