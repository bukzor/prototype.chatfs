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

**Why is `dir_each` evaluated at build time?**
The current builder freezes the tree at `.build()`. Dynamic listings
(e.g. new conversations appearing) are addressed by the planned
[dynamic routing](docs/dev/design-incubators/fusefs-dynamic-routing/)
approach, which uses lazy inode allocation and callback-driven resolution.

**Why does `readdir` report `..` as inode 1 (root)?**
The static node map doesn't track parent relationships. Harmless in
practice — the kernel's dcache tracks parents independently. Will be
fixed by dynamic routing, where the path-based inode table makes
parent lookup trivial.

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
