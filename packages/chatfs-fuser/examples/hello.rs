//! Simplest possible filesystem: one file at the root.
//!
//! ```bash
//! cargo run --example hello -- /tmp/hello
//! cat /tmp/hello/time.txt   # => current timestamp
//! fusermount -u /tmp/hello
//! ```

use chatfs_fuser::prelude::*;

fn main() -> Result<()> {
    let fs = FilesystemBuilder::new()
        .file("time.txt", || {
            format!("{:?}\n", std::time::SystemTime::now())
        })
        .build()?;

    let mountpoint = std::env::args().nth(1).expect("usage: hello <mountpoint>");
    fs.mount(&mountpoint)?;

    Ok(())
}
