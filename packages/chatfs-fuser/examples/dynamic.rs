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

use chatfs_fuser::prelude::*;

fn main() -> Result<()> {
    let hit_count = AtomicU64::new(0);

    let fs = FilesystemBuilder::new()
        .file("time.txt", move || {
            chrono::Local::now().to_rfc3339() + "\n"
        })
        .dir("counters", move |d| {
            // Called when the directory is listed.
            d.file("hits.txt")
             .file("misses.txt")
        }, move |path| {
            // Called when a file within this dir is read.
            match path.file_name() {
                "hits.txt" => {
                    let n = hit_count.fetch_add(1, Ordering::Relaxed);
                    format!("{n}\n")
                }
                _ => String::new(),
            }
        })
        .build()?;

    let mountpoint = std::env::args().nth(1).expect("usage: dynamic <mountpoint>");
    fs.mount(&mountpoint)?;

    Ok(())
}
