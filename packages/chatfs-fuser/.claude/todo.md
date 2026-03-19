<anthropic-skill-ownership llm-subtask />

# chatfs-fuser: path to usable

Goals are examples that work end-to-end. Each item is one commit.

- [ ] `cargo run --example hello` — first working mount
  - [ ] Add fuser dependency
  - [ ] Builder internals: tree storage, inode assignment, store closures
  - [ ] fuser bridge: implement fuser::Filesystem (lookup, getattr, read, readdir)
  - [ ] Mount lifecycle: mount, block, unmount on signal
- [ ] `cargo run --example static_tree` — nested directories
- [ ] `cargo run --example dynamic` — closures in directories
- [ ] `cargo run --example procfs` — full feature set
  - [ ] Symlinks in fuser bridge
  - [ ] mtime/mode passthrough from File metadata
  - [ ] dir_each (dynamic directory templates)

End state: a working FUSE wrapper that chatfs can mount for its org/convo/message
hierarchy. Good enough to use, improve incrementally from there.
