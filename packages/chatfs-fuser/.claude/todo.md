<anthropic-skill-ownership llm-subtask />

# chatfs-fuser: path to usable

Goals are examples that work end-to-end. Each item is one commit.

- [x] `cargo run --example hello` — first working mount
  - [x] Add fuser dep + Node enum (`node.rs`: Dir{children} | File{read closure})
  - [x] Builder: `new()`, `file()`, `build()` — inode alloc, store closures
    - stub API fix: `file()` closure gets `Send + Sync + 'static` bounds
  - [x] fuser bridge (`fuse_impl.rs`): `impl fuser::Filesystem` (lookup, getattr, readdir, read)
  - [x] Wire `mount(self, path)` → `fuser::mount2`, mkdir mountpoint
    - stub API fix: `mount(&self)` → `mount(self)` (fuser consumes the impl)
- [x] `cargo run --example static_tree` — nested directories
- [x] `cargo run --example dynamic` — closures in directories (worked with no changes)
- [x] `cargo run --example procfs` — full feature set
  - [x] Symlinks in fuser bridge
  - [x] mtime/mode passthrough from File metadata (worked from initial impl)
  - [x] dir_each (build-time expansion, `/` merges into parent)
  - [x] Slash-separated paths in dir() (e.g. `dir("sys/vm", ...)`)

End state: a working FUSE wrapper that chatfs can mount for its org/convo/message
hierarchy. Good enough to use, improve incrementally from there.

## Testing

- [x] Refactor: separate pure node-tree logic from FUSE reply dispatch
  - Extract `do_lookup`, `do_getattr`, `do_read`, `do_readlink`, `do_readdir` returning `Result<T, Errno>`
  - `impl Filesystem` becomes a trivial adapter (no logic to test)
- [x] Unit tests: builder tree construction (no FUSE needed)
- [x] Unit tests: node-tree operations (depends on refactor above)
- [x] Integration tests: real FUSE mounts for the four examples

See `TESTING.md` for detailed test plan.

## Known limitations (revisit with user)

- [x] `getattr` calls the read closure on every stat — by design
  - Applications that care should cache in their callback; FUSE TTL covers the common case
- [ ] `dir_each` evaluates `list_fn` at build time, not readdir time
  - Truly dynamic directories need lazy inode allocation (interior mutability on node map)
- [ ] `readdir` `..` entry always reports inode 1 (root) regardless of actual parent
  - Works in practice (kernel tracks parents via dcache) but not strictly correct
- [ ] No `open`/`release` tracking — every `read` calls the closure fresh
  - Fine for cheap closures; expensive ones may want per-open caching
