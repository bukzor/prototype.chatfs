# chatfs-fuser Testing Log

Tests performed during initial implementation (2026-03-19).

## Build checks

Every commit was verified with `cargo check` before committing:

```bash
cargo check -p chatfs-fuser                    # lib compiles
cargo check -p chatfs-fuser --example hello    # example compiles
cargo check -p chatfs-fuser --example static_tree
cargo check -p chatfs-fuser --example dynamic
cargo check -p chatfs-fuser --example procfs
```

Final state: zero warnings across lib and all examples.

## End-to-end mount tests

### hello

```bash
cargo run -p chatfs-fuser --example hello -- /tmp/hello_fs &
sleep 2
ls /tmp/hello_fs/          # => time.txt
cat /tmp/hello_fs/time.txt # => SystemTime { tv_sec: ..., tv_nsec: ... }
fusermount -u /tmp/hello_fs
```

**Result:** Pass. File listed, content is a timestamp, clean unmount.

### static_tree

```bash
cargo run -p chatfs-fuser --example static_tree -- /tmp/tree_fs &
sleep 2
ls /tmp/tree_fs/              # => docs  README.md
cat /tmp/tree_fs/README.md    # => # My Project
ls /tmp/tree_fs/docs/         # => api.md  guide.md
cat /tmp/tree_fs/docs/api.md  # => # API Reference
cat /tmp/tree_fs/docs/guide.md # => # User Guide\n\nGetting started...
fusermount -u /tmp/tree_fs
```

**Result:** Pass. Nested directory, all files readable.

### dynamic

```bash
cargo run -p chatfs-fuser --example dynamic -- /tmp/dyn_fs &
sleep 2
ls /tmp/dyn_fs/                      # => counters  time.txt
cat /tmp/dyn_fs/time.txt             # => SystemTime { ... }
ls /tmp/dyn_fs/counters/             # => hits.txt  misses.txt
cat /tmp/dyn_fs/counters/hits.txt    # => 3   (increments on each read)
cat /tmp/dyn_fs/counters/hits.txt    # => 8   (higher — getattr also calls closure)
cat /tmp/dyn_fs/counters/hits.txt    # => 13
cat /tmp/dyn_fs/counters/misses.txt  # => (empty, String::new)
fusermount -u /tmp/dyn_fs
```

**Result:** Pass. Counter increments across reads. Jumps by >1 because
`getattr` also invokes the read closure (to determine file size). This is
expected — see known limitations in todo.md.

### procfs

```bash
cargo run -p chatfs-fuser --example procfs -- /tmp/proc_fs &
sleep 2

# Root listing
ls -la /tmp/proc_fs/
# => 1/  42/  meminfo  self@  sys/  uptime

# Symlink
readlink /tmp/proc_fs/self  # => <current PID>

# File with metadata
cat /tmp/proc_fs/uptime          # => 12345.67 98765.43
stat -c '%a' /tmp/proc_fs/uptime # => 444  (mode from File::mode(0o444))

# Simple file
cat /tmp/proc_fs/meminfo  # => MemTotal: 16384 kB

# Slash-separated dir path
ls /tmp/proc_fs/sys/              # => vm
ls /tmp/proc_fs/sys/vm/           # => swappiness
cat /tmp/proc_fs/sys/vm/swappiness # => 60

# dir_each: dynamic pid directories
ls /tmp/proc_fs/1/         # => cmdline  exe  status
cat /tmp/proc_fs/1/status  # => Pid: 1
cat /tmp/proc_fs/1/cmdline # => /usr/bin/1
readlink /tmp/proc_fs/1/exe # => /usr/bin/1

cat /tmp/proc_fs/42/status  # => Pid: 42
readlink /tmp/proc_fs/42/exe # => /usr/bin/42

fusermount -u /tmp/proc_fs
```

**Result:** Pass. All features work: symlinks, metadata, nested paths,
dir_each with template closures, symlinks inside templates.

## Design validation (pre-implementation)

Before writing code, the fuser 0.17 API was examined via `rustdoc-json`
to validate the stub API design:

- **`fuser::Filesystem` trait methods:** Confirmed minimum set needed
  (lookup, getattr, readdir, read) — all others have default ENOSYS impls.
- **`fuser::mount2` signature:** Takes filesystem by value + `&Config`.
  Confirmed `mount(&self)` stub needed to change to `mount(self)`.
- **`FileAttr` fields:** 15 fields (ino, size, blocks, times, kind, perm,
  nlink, uid, gid, rdev, blksize, flags). Confirmed `File` struct's
  `data`/`mtime`/`mode` are sufficient — rest synthesized with defaults.
- **fuser 0.17 newtypes:** `INodeNo`, `FileHandle`, `LockOwner`,
  `OpenFlags`, `Generation`, `Errno` — all tuple structs, used instead
  of raw integers.
- **`&self` not `&mut self`:** fuser 0.17 Filesystem trait methods take
  `&self` (changed from older versions that used `&mut self`).
- **`Request` has no lifetime parameter** in 0.17 (changed from older
  `Request<'_>`).

## Mental trace-throughs

Reasoning through code logic without running it. Listed here because
some traces were **wrong** — the end-to-end tests caught what the
traces missed.

### wrap_in_path segment ordering (WRONG, then corrected)

First implementation used `parts.iter().rev().skip(1)`. Mental trace
for `path = "sys/vm"`:

> parts = ["sys", "vm"]
> entry = Dir{user_entries}  — the "vm" directory
> Loop: rev().skip(1) = ["sys"]:
>   entry = Dir{entries: [("vm", Dir{user_entries})]}
> Return ("sys", Dir{...})
>
> "That's correct."

**This trace was wrong.** The code actually used the loop variable
`segment` (which was `"sys"`) as the child name, not `"vm"`. The
trace substituted the desired output rather than following the actual
code. End-to-end test showed `ls /tmp/proc_fs/sys/` → `sys` instead
of `vm`, revealing the bug.

Second trace (post-failure) correctly identified: `rev().skip(1)` on
`["sys", "vm"]` yields `["sys"]`, so the loop wraps with name `"sys"`
— creating `sys/sys/` not `sys/vm/`. Fix: `parts[1..].iter().rev()`
yields `["vm"]`, wrapping correctly.

**Lesson:** Mental traces are unreliable when the tracer already has a
desired outcome in mind. The end-to-end test was essential.

### readdir `..` inode (accepted, not fixed)

Noted that `readdir` hardcodes `..` inode as 1 (root) for all
directories, even nested ones. Traced through the FUSE protocol
behavior: the kernel tracks parent inodes via dcache from `lookup`
calls, so it doesn't rely on the `..` inode from `readdir`. Accepted
as cosmetically wrong but functionally correct. Documented in todo.md
known limitations.

### dynamic example closure bounds (correct)

Before testing the `dynamic` example, traced through the type bounds:
`Arc<AtomicU64>` implements `Send + Sync + 'static`, `move ||`
closures capturing it satisfy the `Fn() -> R + Send + Sync + 'static`
bound on `file()`, `String::new` as a function pointer is
`fn() -> String` which implements `Fn + Send + Sync + 'static`.
Conclusion: should compile with no changes. **Confirmed by test.**

### getattr calling read closures (accepted)

Identified that `getattr` calls the file's read closure on every stat
to determine file size. For the `dynamic` example, this means the
`hits.txt` counter increments on `stat` as well as `cat`. Traced
through `cat` behavior: kernel does `open` → `getattr` → `read` →
`close`, so each `cat` triggers at least one `getattr` + one `read`,
incrementing the counter 2+ times. **Confirmed by test** — counter
jumped by ~5 per `cat` (getattr called multiple times by kernel/VFS
layer).

## Bugs found and fixed during testing

1. **`wrap_in_path` reversed wrong segments** — `dir("sys/vm", ...)`
   produced `sys/sys/` instead of `sys/vm/`. Fix: iterate `parts[1..]`
   instead of `parts.iter().rev().skip(1)`.

2. **Rust 2024 edition pattern matching** — `for (name, &child_ino)` in
   a `&Vec` reference is rejected. Fix: `for (name, child_ino)` then
   `let child_ino = **child_ino;`.

3. **`suspicious_double_ref_op` warning** — `.clone()` on `&&String`
   clones the reference, not the string. Fix: `(*name).clone()`.

## Planned refactoring: separate pure node-tree logic from FUSE plumbing

### Problem

`fuse_impl.rs` mixes two concerns in every method:

1. **Pure computation** on the node map (resolve names, build attrs,
   slice data, list entries)
2. **FUSE reply dispatch** (unwrap `INodeNo`, call `reply.entry/error/data`)

fuser's `Reply*` types are concrete and tied to an internal channel —
they can't be constructed in tests. This makes the pure logic untestable
without a real FUSE mount.

### Refactor

Extract the pure computation into methods on `FuseFs` (or a new
`NodeTree` type) that return `Result<T, Errno>`. The `impl Filesystem`
becomes a thin adapter:

```rust
// Pure — testable without FUSE
impl FuseFs {
    fn do_lookup(&self, parent: u64, name: &str, uid: u32, gid: u32)
        -> Result<(FileAttr, Generation), Errno> { ... }

    fn do_getattr(&self, ino: u64, uid: u32, gid: u32)
        -> Result<FileAttr, Errno> { ... }

    fn do_read(&self, ino: u64, offset: u64, size: u32)
        -> Result<Vec<u8>, Errno> { ... }

    fn do_readlink(&self, ino: u64)
        -> Result<String, Errno> { ... }

    fn do_readdir(&self, ino: u64, offset: u64)
        -> Result<Vec<(u64, FileType, String)>, Errno> { ... }
}

// Adapter — trivially correct, no logic to test
impl Filesystem for FuseFs {
    fn lookup(&self, req, parent, name, reply) {
        match self.do_lookup(u64::from(parent), name.to_str().unwrap(), req.uid(), req.gid()) {
            Ok((attr, gen)) => reply.entry(&TTL, &attr, gen),
            Err(e) => reply.error(e),
        }
    }
    // ... same pattern for all methods
}
```

`FileAttr`, `FileType`, `Errno`, `Generation` are plain value types —
using them in the pure layer doesn't introduce IO coupling.

### What this enables

The `do_*` methods can be called directly in `#[test]` functions with
a hand-built `HashMap<u64, Node>`. No `/dev/fuse`, no `fusermount`, no
`sleep`, no process management.

## Test plan

Two test suites, covering all items from the manual and mental testing
above.

### Suite 1: Unit tests (`cargo test`, no FUSE)

Builder tree construction and pure node-tree operations. Each test
builds a `FilesystemBuilder`, calls `.build()`, and either inspects
the `HashMap<u64, Node>` directly or calls the `do_*` methods.

**Builder tests** (test `build()` output — the `HashMap<u64, Node>`):

- `build_empty` — empty builder produces root dir (inode 1) with no
  children
- `build_single_file` — one `.file()` produces root with one child,
  child is `Node::File`, inode 2
- `build_inode_sequence` — multiple entries get sequential inodes from 2
- `build_nested_dir` — `.dir("d", |d| d.file("f", ...))` produces
  correct parent→child inode relationships
- `build_symlink` — `.symlink()` produces `Node::Symlink`
- `build_wrap_in_path` — `dir("a/b/c", ...)` produces three nested
  `Node::Dir`s with correct names at each level
- `build_wrap_in_path_single` — `dir("x", ...)` produces one dir named
  `"x"` (no nesting)
- `build_dir_each` — `dir_each("pids", list, template)` expands entries
  at build time, each with correct template-generated children
- `build_dir_each_root_merge` — `dir_each("/", list, template)` merges
  entries into parent rather than creating a subdirectory

**Node-tree operation tests** (require the pure/FUSE separation
refactor above):

- `lookup_existing` — returns correct `FileAttr` for a known child
- `lookup_missing` — returns `Errno::ENOENT` for unknown name
- `lookup_not_a_dir` — returns `Errno::ENOENT` when parent is a file
- `getattr_root` — root inode returns `FileType::Directory`, perm 0o555
- `getattr_file` — file inode returns `FileType::RegularFile`, size
  from closure output, perm from `File::mode` or default 0o444
- `getattr_symlink` — symlink inode returns `FileType::Symlink`, size
  from target length
- `read_full` — offset 0, size >= data len → full content
- `read_offset` — offset into data → correct slice
- `read_past_end` — offset >= data len → empty
- `read_partial` — offset + size < data len → correct window
- `readlink_valid` — returns target string from closure
- `readlink_not_symlink` — returns `Errno::ENOENT` for file inode
- `readdir_root` — returns `.`, `..`, then children sorted by name
- `readdir_offset` — offset skips initial entries
- `readdir_types` — directories, files, and symlinks report correct
  `FileType`
- `readdir_not_a_dir` — returns `Errno::ENOENT` for file inode

### Suite 2: Integration tests (real FUSE mount)

These test the full stack including the kernel VFS layer. Slower, require
`/dev/fuse` access. Use `spawn_mount2` for non-blocking mounts in test
harness.

After the refactor, these exist primarily to catch:
- fuser adapter wiring bugs (wrong argument passed to `do_*`)
- kernel/VFS behavior differences from expectations
- mount/unmount lifecycle issues

Each of the four example scenarios becomes one integration test:

- `mount_hello` — mount, ls root, cat file, unmount
- `mount_static_tree` — mount, ls nested dirs, cat files, unmount
- `mount_dynamic` — mount, verify closure re-evaluation on read
- `mount_procfs` — mount, readlink symlink, stat metadata, ls dir_each
  entries, cat templated files, unmount

These are essentially the manual tests from above, automated.
