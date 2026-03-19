//! Simplified /proc reproduction — stress-tests the API design.
//!
//! Surfaces: symlinks, metadata control, dynamic directory listing,
//! parameterized paths, writable files.
//!
//! ```bash
//! cargo run --example procfs -- /tmp/proc
//! ls /tmp/proc/             # => self@  uptime  meminfo  sys/  1/  42/  ...
//! readlink /tmp/proc/self   # => 42  (current pid)
//! cat /tmp/proc/uptime      # => "12345.67 98765.43\n"
//! cat /tmp/proc/1/status    # => "Name: init\nPid: 1\n..."
//! stat /tmp/proc/uptime     # => mtime reflects boot time
//! echo 60 > /tmp/proc/sys/vm/swappiness
//! ```

use chatfs_fuser::prelude::*;

fn main() -> Result<()> {
    let fs = FilesystemBuilder::new()
        // Static symlink.
        .symlink("self", || format!("{}", std::process::id()))

        // File with metadata — callback returns FileContent.
        .file("uptime", || {
            FileContent::new(read_uptime())
                .mtime(boot_time())
                .mode(0o444)
        })

        // Simple case — callback returns String, auto-converts.
        .file("meminfo", || read_meminfo())

        // Writable file — read closure + write closure.
        .dir("sys/vm", |d| {
            d.file("swappiness",
                || read_sysctl("vm.swappiness"),
                |bytes| write_sysctl("vm.swappiness", bytes),
            )
        })

        // Dynamic directory listing: entries computed at readdir time.
        .dir_each("/", || list_pids(), |pid, d| {
            d.file("status", move || {
                FileContent::new(format!("Pid: {pid}\n"))
                    .mtime(proc_start_time(pid))
            })
            .file("cmdline", move || read_cmdline(pid))
            .symlink("exe", move || read_exe_path(pid))
        })

        .build()?;

    let mountpoint = std::env::args().nth(1).expect("usage: procfs <mountpoint>");
    fs.mount(&mountpoint)?;

    Ok(())
}

// -- stubs --
fn boot_time() -> std::time::SystemTime { std::time::SystemTime::now() }
fn proc_start_time(_pid: &str) -> std::time::SystemTime { std::time::SystemTime::now() }
fn read_uptime() -> String { "12345.67 98765.43\n".into() }
fn read_meminfo() -> String { "MemTotal: 16384 kB\n".into() }
fn list_pids() -> Vec<String> { vec!["1".into(), "42".into()] }
fn read_cmdline(pid: &str) -> String { format!("/usr/bin/{pid}\n") }
fn read_exe_path(pid: &str) -> String { format!("/usr/bin/{pid}") }
fn read_sysctl(_key: &str) -> String { "60\n".into() }
fn write_sysctl(_key: &str, _value: &[u8]) {}
