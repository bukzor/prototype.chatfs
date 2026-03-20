# chatfs-fuser

A declarative builder for read-only FUSE filesystems, built on [`fuser`](https://docs.rs/fuser).

Define files as closures. The closure runs on each read, so content is always fresh.
Directories, symlinks, and metadata (mtime, mode) are also supported.

## Usage

```rust
use chatfs_fuser::prelude::*;

fn main() -> Result<()> {
    let fs = FilesystemBuilder::new()
        .file("time.txt", || {
            format!("{:?}\n", std::time::SystemTime::now())
        })
        .dir("counters", |d| {
            d.file("hits.txt", || "0\n");
        })
        .build()?;

    fs.mount("/tmp/my_fs")?;
    Ok(())
}
```

Every `cat /tmp/my_fs/time.txt` calls the closure, returning the current time.

## API

**`FilesystemBuilder`** — chain calls to define the tree, then `.build()` to get a `Filesystem`.

- `.file(name, closure)` — read-only file. Closure returns `impl Into<File>` (`&str`, `String`, or `File` with metadata).
- `.dir(name, |d| { ... })` — static directory. Name supports `/` for nested paths (e.g. `"sys/vm"`).
- `.dir_each(name, list_fn, |item, d| { ... })` — templated directory. `list_fn` produces entry names, `template_fn` builds each entry's subtree.
- `.symlink(name, closure)` — symbolic link. Closure returns the target path.

**`File`** — file content with optional metadata.

```rust
File::new("content")
    .mtime(SystemTime::now())
    .mode(0o444)
```

**`Filesystem`** — the built tree.

- `.mount(path)` — mount and block until unmounted (e.g. `fusermount -u path`).

## Examples

```bash
cargo run --example hello -- /tmp/hello         # one file
cargo run --example static_tree -- /tmp/tree    # nested directories
cargo run --example dynamic -- /tmp/dyn         # closures with shared state
cargo run --example procfs -- /tmp/proc         # symlinks, metadata, dir_each
```

## FAQ

**Why does the read closure run on every `stat`, `read`, etc.?**
By design. The framework is intentionally stateless — no result caching,
no `open`/`release` tracking. `stat` calls the closure to determine file
size; `read` calls it per FUSE buffer chunk (~128KB). This keeps the
framework simple and correct. If re-invocation is expensive, cache in
your closure. FUSE kernel caching (TTL) also helps.

**How does `dir_each` work?**
`dir_each` is a builder convenience — it expands at `.build()` time into
a `Dir` whose `read` closure calls your `list_fn` on every access.
Directory listings are always fresh; no rebuild needed.

**Does `readdir` preserve ordering?**
Yes. Directory entries appear in the order your closure inserts them
(`DirEntries` is backed by `IndexMap`). The framework does not sort.

**How does `readdir` resolve `..`?**
The inode table tracks path→inode mappings. Parent inodes are derived
by stripping the last path segment. `..` always reports the correct
parent inode.

**What happens when a file disappears between accesses?**
If an inode was allocated (via `lookup` or `readdir`) but its path no
longer resolves — e.g. a `dir_each` list shrank — subsequent operations
return `ESTALE` (stale file handle), not `ENOENT`.

## Future work

- **`touch` as sync trigger (`setattr`/`utimens`).**
  `touch conversations/abc123.md` would enqueue a cache refresh for that
  conversation. Maps naturally to filesystem semantics — works with `make`,
  `find -exec touch`, etc.

- **Writable control files (`write`).**
  Virtual files like `control` (write `sync <conv>` to trigger refresh)
  and `status` (read daemon state). Uses procfs/sysfs patterns for the
  control plane.

- **Write operations for chat content.**
  Append messages, fork conversations, amend messages. Blocked on
  resolving the fork representation design.
