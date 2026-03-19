//! Simplest possible filesystem: one file at the root.
//!
//! ```bash
//! cargo run --example hello -- /tmp/hello_fs
//! cat /tmp/hello_fs/time.txt   # => current timestamp
//! fusermount -u /tmp/hello_fs
//! ```

use chatfs_fuser::prelude::*;

fn main() -> Result<()> {
    let fs = FilesystemBuilder::new()
        .file("time.txt", || {
            format!("{:?}\n", std::time::SystemTime::now())
        })
        .build()?;

    fs.mount("/tmp/hello_fs")?;

    Ok(())
}
