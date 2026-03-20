<anthropic-skill-ownership llm-subtask />

# chatfs-fuser

- [ ] Dynamic routing — lazy inode allocation via `PathSegment` tree
  - After: update README.md (API section, examples, FAQ) to reflect new API
  - Design: `docs/design-incubators/dynamic-routing/`
  - Policies: `docs/technical-policy.kb/`, `docs/technical-policy.kb/caller-responsibility.kb/`
  - Key decisions:
    - Unified `PathSegment` enum: `Dir { read: Fn() -> HashMap }`, `File { read }`, `Symlink { read }`
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
  - [ ] Update README.md — FAQ entries (lines ~69–79) describe now-fixed behaviors
