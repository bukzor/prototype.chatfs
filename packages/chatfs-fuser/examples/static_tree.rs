//! Static content as the degenerate case — &str coerces to a constant closure.
//!
//! Shows that the same `.file()` API accepts both closures and string literals.
//!
//! ```bash
//! cargo run --example static_tree -- /tmp/tree_fs
//! cat /tmp/tree_fs/README.md   # => "# My Project\n"
//! cat /tmp/tree_fs/docs/api.md # => "# API Reference\n"
//! ```

use chatfs_fuser::prelude::*;

fn main() -> Result<()> {
    let fs = FilesystemBuilder::new()
        // Static string — degenerate case, same API.
        .file("README.md", "# My Project\n")
        .dir("docs", |d| {
            d.file("guide.md", "# User Guide\n\nGetting started...\n")
             .file("api.md", "# API Reference\n")
        })
        .build()?;

    let mountpoint = std::env::args().nth(1).expect("usage: static_tree <mountpoint>");
    fs.mount(&mountpoint)?;

    Ok(())
}
