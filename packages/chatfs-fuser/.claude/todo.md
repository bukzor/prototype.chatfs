<anthropic-skill-ownership llm-subtask />

# chatfs-fuser

- [ ] Dynamic routing — lazy inode allocation via `PathSegment` tree
  - After: update README.md (API section, examples, FAQ) to reflect new API
  - Design: `docs/design-incubators/dynamic-routing/`
  - Policies: `docs/technical-policy.kb/`, `docs/technical-policy.kb/caller-responsibility.kb/`
  - Key decisions:
    - Unified `PathSegment` enum: `Dir { read: Fn() -> HashMap }`, `File { read }`, `Symlink { read }`
    - No static/dynamic split — all variants are closures, static is just a constant-returning closure
    - No `dir_each` — callers compose list+template in their `Dir` callback
    - `entry_valid=0` / `attr_valid=0` already implemented (TTL=0 in fuse_impl.rs)
  - [ ] Update Python sketch (`docs/design-incubators/dynamic-routing/demo.py`) to unified design
    - Replace `StaticDir`/`DynamicDir` with single `Dir(read: Callable[[], dict])`
    - All variants use `read` callback. Validate before porting to Rust.
  - [ ] Add `PathSegment` enum — three variants, all closure-driven. Unit tests.
  - [ ] Add `InodeTable` — bidirectional path↔ino map, `ensure_ino()`, `path_of()`. Unit tests.
  - [ ] Add `resolve_entry()` — walk path through `PathSegment` tree. Unit tests.
  - [ ] Replace `NodeOps` + Builder internals — `PathSegment` tree + `InodeTable` replaces
    `HashMap<u64, Node>` + `flatten()`. Delete `Node`, `dir_each`. Update all tests.
  - [ ] ESTALE for stale inodes — inode in table but path doesn't resolve → ESTALE not ENOENT
  - [ ] Correct `readdir` `..` inode — derive parent from `InodeTable` path

