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
- [ ] `cargo run --example static_tree` — nested directories
- [ ] `cargo run --example dynamic` — closures in directories
- [ ] `cargo run --example procfs` — full feature set
  - [ ] Symlinks in fuser bridge
  - [ ] mtime/mode passthrough from File metadata
  - [ ] dir_each (dynamic directory templates)

End state: a working FUSE wrapper that chatfs can mount for its org/convo/message
hierarchy. Good enough to use, improve incrementally from there.
