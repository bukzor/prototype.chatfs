<anthropic-skill-ownership llm-subtask />

# chatfs-fuser

- [x] Dynamic routing — lazy inode allocation via `PathSegment` tree
  - Design: `docs/design-incubators/dynamic-routing/`
  - Policies: `docs/technical-policy.kb/`, `docs/technical-policy.kb/caller-responsibility.kb/`
  - Key decisions:
    - Unified `Path` enum: `Dir { read: Fn() -> DirEntries }`, `File { read }`, `Symlink { read }`
    - No static/dynamic split — all variants are closures (Arc-wrapped, cheap Clone)
    - `dir_each` kept as builder convenience — pure composition over `.dir()`
    - `entry_valid=0` / `attr_valid=0` already implemented (TTL=0 in fuse_impl.rs)
    - `INodeNo` used throughout (no raw u64 conversions)
  - [x] Update Python sketch to unified design
  - [x] Add `PathSegment` enum
  - [x] Add `InodeTable`
  - [x] Add `resolve_stale()` (née `resolve_and_read()`)
  - [x] Replace `NodeOps` + Builder internals
  - [x] Correct `readdir` `..` inode (parent_ino from InodeTable)
  - [x] Use `INodeNo` throughout instead of raw u64
  - [x] ESTALE for stale inodes — `resolve()` wraps `resolve_stale()`, any error → ESTALE
  - [x] Update README.md FAQ and caller-responsibility.kb docs to reflect implemented state
- [x] API cleanup — rename and preserve caller ordering
  - [x] `PathSegment` → `Path`
  - [x] `HashMap<String, PathSegment>` → `DirEntries` (backed by `IndexMap`, preserves insertion order)
  - [x] Remove alphabetical sort in `do_readdir` — respect caller ordering
  - [x] Delete `caller-responsibility.kb/entry-ordering.md` and `dir-each-composition.md` (done in prior commit)
