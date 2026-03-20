//! Integration tests: mount example binaries and verify via the real filesystem.
//!
//! Each test spawns an example binary, waits for the FUSE mount, runs assertions
//! against the mountpoint, then tears down. Requires `/dev/fuse` access.

use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Child, Command};
use std::time::{Duration, Instant};

use anyhow::Result;

/// RAII guard that unmounts and kills the child process on drop.
struct MountGuard {
    child: Child,
    mountpoint: PathBuf,
}

impl MountGuard {
    /// Spawn an example binary with the given mountpoint and wait for FUSE to be ready.
    fn spawn(example: &str, mountpoint: &Path) -> Result<Self> {
        fs::create_dir_all(mountpoint)?;

        let child = Command::new(env!("CARGO"))
            .args(["run", "--example", example, "--"])
            .arg(mountpoint)
            .spawn()?;

        let guard = Self {
            child,
            mountpoint: mountpoint.to_owned(),
        };

        // Wait for FUSE mount to become ready by polling readdir on the mountpoint.
        // A freshly-created dir is empty; once FUSE mounts, entries appear.
        let deadline = Instant::now() + Duration::from_secs(30);
        loop {
            if let Ok(mut entries) = fs::read_dir(mountpoint)
                && entries.next().is_some()
            {
                break;
            }
            anyhow::ensure!(
                Instant::now() < deadline,
                "timed out waiting for {example} to mount at {}",
                mountpoint.display()
            );
            std::thread::sleep(Duration::from_millis(50));
        }

        Ok(guard)
    }
}

impl Drop for MountGuard {
    fn drop(&mut self) {
        let _ = Command::new("fusermount")
            .args(["-u"])
            .arg(&self.mountpoint)
            .status();
        let _ = self.child.kill();
        let _ = self.child.wait();
    }
}

fn read_dir_sorted(path: &Path) -> Result<Vec<String>> {
    let mut entries: Vec<String> = fs::read_dir(path)?
        .map(|e| e.map(|e| e.file_name().to_string_lossy().into_owned()))
        .collect::<std::io::Result<_>>()?;
    entries.sort();
    Ok(entries)
}

#[test]
fn mount_hello() -> Result<()> {
    let tmp = tempfile::TempDir::new()?;
    let mnt = tmp.path().join("mnt");
    let _guard = MountGuard::spawn("hello", &mnt)?;

    let entries = read_dir_sorted(&mnt)?;
    assert_eq!(entries, ["time.txt"]);

    let content = fs::read_to_string(mnt.join("time.txt"))?;
    assert!(
        content.contains("tv_sec"),
        "expected SystemTime debug output, got: {content}"
    );
    Ok(())
}

#[test]
fn mount_static_tree() -> Result<()> {
    let tmp = tempfile::TempDir::new()?;
    let mnt = tmp.path().join("mnt");
    let _guard = MountGuard::spawn("static_tree", &mnt)?;

    let entries = read_dir_sorted(&mnt)?;
    assert_eq!(entries, ["README.md", "docs"]);

    assert_eq!(fs::read_to_string(mnt.join("README.md"))?, "# My Project\n");

    let doc_entries = read_dir_sorted(&mnt.join("docs"))?;
    assert_eq!(doc_entries, ["api.md", "guide.md"]);

    assert_eq!(fs::read_to_string(mnt.join("docs/api.md"))?, "# API Reference\n");
    assert_eq!(
        fs::read_to_string(mnt.join("docs/guide.md"))?,
        "# User Guide\n\nGetting started...\n"
    );
    Ok(())
}

#[test]
fn mount_dynamic() -> Result<()> {
    let tmp = tempfile::TempDir::new()?;
    let mnt = tmp.path().join("mnt");
    let _guard = MountGuard::spawn("dynamic", &mnt)?;

    let entries = read_dir_sorted(&mnt)?;
    assert_eq!(entries, ["counters", "time.txt"]);

    let content = fs::read_to_string(mnt.join("time.txt"))?;
    assert!(content.contains("tv_sec"), "expected timestamp, got: {content}");

    let v1: u64 = fs::read_to_string(mnt.join("counters/hits.txt"))?.trim().parse()?;
    let v2: u64 = fs::read_to_string(mnt.join("counters/hits.txt"))?.trim().parse()?;
    assert!(v2 > v1, "counter should increment: v1={v1}, v2={v2}");

    assert_eq!(fs::read_to_string(mnt.join("counters/misses.txt"))?, "");
    Ok(())
}

#[test]
fn mount_procfs() -> Result<()> {
    let tmp = tempfile::TempDir::new()?;
    let mnt = tmp.path().join("mnt");
    let _guard = MountGuard::spawn("procfs", &mnt)?;

    let entries = read_dir_sorted(&mnt)?;
    assert_eq!(entries, ["1", "42", "meminfo", "self", "sys", "uptime"]);

    // Symlink — points to the PID of the example binary, not the test process.
    let target = fs::read_link(mnt.join("self"))?;
    let target_pid: u32 = target.to_string_lossy().parse()?;
    assert!(target_pid > 0, "symlink target should be a valid PID");

    assert_eq!(fs::read_to_string(mnt.join("uptime"))?, "12345.67 98765.43\n");
    assert_eq!(fs::read_to_string(mnt.join("meminfo"))?, "MemTotal: 16384 kB\n");

    let sys_entries = read_dir_sorted(&mnt.join("sys"))?;
    assert_eq!(sys_entries, ["vm"]);
    assert_eq!(fs::read_to_string(mnt.join("sys/vm/swappiness"))?, "60\n");

    // dir_each: pid directories
    assert_eq!(fs::read_to_string(mnt.join("1/status"))?, "Pid: 1\n");
    assert_eq!(fs::read_to_string(mnt.join("1/cmdline"))?, "/usr/bin/1\n");
    assert_eq!(fs::read_link(mnt.join("1/exe"))?.to_string_lossy(), "/usr/bin/1");

    assert_eq!(fs::read_to_string(mnt.join("42/status"))?, "Pid: 42\n");
    assert_eq!(fs::read_link(mnt.join("42/exe"))?.to_string_lossy(), "/usr/bin/42");
    Ok(())
}
