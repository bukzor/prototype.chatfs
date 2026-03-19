//! Filesystem backed by closures — the typical use case.
//!
//! Directory listings and file contents come from external sources.
//! This is how chatfs actually uses the crate.
//!
//! ```bash
//! cargo run --example dynamic -- /tmp/dyn_fs
//! ls /tmp/dyn_fs/            # => time.txt  counters/
//! cat /tmp/dyn_fs/time.txt   # => current timestamp
//! ls /tmp/dyn_fs/counters/   # => hits.txt  misses.txt
//! cat /tmp/dyn_fs/counters/hits.txt  # => "0\n", "1\n", "2\n", ...
//! ```

use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;

use chatfs_fuser::prelude::*;

fn main() -> Result<()> {
    let hit_count = Arc::new(AtomicU64::new(0));

    let fs = FilesystemBuilder::new()
        .file("time.txt", || {
            format!("{:?}\n", std::time::SystemTime::now())
        })
        .dir("counters", move |d| {
            let hit_count = Arc::clone(&hit_count);
            d.file("hits.txt", move || {
                let n = hit_count.fetch_add(1, Ordering::Relaxed);
                format!("{n}\n")
            })
            .file("misses.txt", String::new);
        })
        .build()?;

    let mountpoint = std::env::args().nth(1).expect("usage: dynamic <mountpoint>");
    fs.mount(&mountpoint)?;

    Ok(())
}
