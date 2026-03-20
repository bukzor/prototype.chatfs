use fuser::{Errno, FileType};

use crate::node_ops::NodeOps;
use crate::FilesystemBuilder;

const UID: u32 = 1000;
const GID: u32 = 1000;

/// Helper: build and return a `NodeOps`.
fn build(builder: FilesystemBuilder) -> NodeOps {
    NodeOps::new(builder.build().expect("build failed").nodes)
}

// --- lookup ---

#[test]
fn lookup_existing() -> Result<(), Errno> {
    let ops = build(FilesystemBuilder::new().file("hello.txt", || "hi"));
    let (attr, _gen) = ops.do_lookup(1, "hello.txt", UID, GID)?;
    assert_eq!(attr.kind, FileType::RegularFile);
    assert_eq!(attr.size, 2); // "hi"
    Ok(())
}

#[test]
fn lookup_missing() {
    let ops = build(FilesystemBuilder::new().file("hello.txt", || "hi"));
    assert!(ops.do_lookup(1, "nope", UID, GID).is_err());
}

#[test]
fn lookup_not_a_dir() {
    let ops = build(FilesystemBuilder::new().file("f", || "data"));
    // inode 2 is the file, not a directory
    assert!(ops.do_lookup(2, "child", UID, GID).is_err());
}

// --- getattr ---

#[test]
fn getattr_root() -> Result<(), Errno> {
    let ops = build(FilesystemBuilder::new());
    let attr = ops.do_getattr(1, UID, GID)?;
    assert_eq!(attr.kind, FileType::Directory);
    assert_eq!(attr.perm, 0o555);
    assert_eq!(attr.uid, UID);
    assert_eq!(attr.gid, GID);
    Ok(())
}

#[test]
fn getattr_file() -> Result<(), Errno> {
    let ops = build(FilesystemBuilder::new().file("f", || "hello"));
    let attr = ops.do_getattr(2, UID, GID)?;
    assert_eq!(attr.kind, FileType::RegularFile);
    assert_eq!(attr.size, 5);
    assert_eq!(attr.perm, 0o444); // default
    Ok(())
}

#[test]
fn getattr_file_custom_mode() -> Result<(), Errno> {
    let ops = build(
        FilesystemBuilder::new().file("f", || crate::File::new("x").mode(0o644)),
    );
    let attr = ops.do_getattr(2, UID, GID)?;
    assert_eq!(attr.perm, 0o644);
    Ok(())
}

#[test]
fn getattr_symlink() -> Result<(), Errno> {
    let ops = build(FilesystemBuilder::new().symlink("link", || "/target".to_owned()));
    let attr = ops.do_getattr(2, UID, GID)?;
    assert_eq!(attr.kind, FileType::Symlink);
    assert_eq!(attr.size, 7); // "/target"
    Ok(())
}

#[test]
fn getattr_missing() {
    let ops = build(FilesystemBuilder::new());
    assert!(ops.do_getattr(999, UID, GID).is_err());
}

// --- read ---

#[test]
fn read_full() -> Result<(), Errno> {
    let ops = build(FilesystemBuilder::new().file("f", || "hello world"));
    let data = ops.do_read(2, 0, 1024)?;
    assert_eq!(data, b"hello world");
    Ok(())
}

#[test]
fn read_offset() -> Result<(), Errno> {
    let ops = build(FilesystemBuilder::new().file("f", || "hello world"));
    let data = ops.do_read(2, 6, 1024)?;
    assert_eq!(data, b"world");
    Ok(())
}

#[test]
fn read_past_end() -> Result<(), Errno> {
    let ops = build(FilesystemBuilder::new().file("f", || "hi"));
    let data = ops.do_read(2, 100, 1024)?;
    assert!(data.is_empty());
    Ok(())
}

#[test]
fn read_partial() -> Result<(), Errno> {
    let ops = build(FilesystemBuilder::new().file("f", || "hello world"));
    let data = ops.do_read(2, 0, 5)?;
    assert_eq!(data, b"hello");
    Ok(())
}

#[test]
fn read_not_a_file() {
    let ops = build(FilesystemBuilder::new());
    assert!(ops.do_read(1, 0, 1024).is_err()); // root is a dir
}

// --- readlink ---

#[test]
fn readlink_valid() -> Result<(), Errno> {
    let ops = build(FilesystemBuilder::new().symlink("link", || "/target".to_owned()));
    let data = ops.do_readlink(2)?;
    assert_eq!(data, b"/target");
    Ok(())
}

#[test]
fn readlink_not_symlink() {
    let ops = build(FilesystemBuilder::new().file("f", || "data"));
    assert!(ops.do_readlink(2).is_err());
}

// --- readdir ---

#[test]
fn readdir_root() -> Result<(), Errno> {
    let ops = build(
        FilesystemBuilder::new()
            .file("b", || "b")
            .file("a", || "a"),
    );
    let entries = ops.do_readdir(1, 0)?;
    let names: Vec<&str> = entries.iter().map(|(_, _, n)| n.as_str()).collect();
    assert_eq!(names, vec![".", "..", "a", "b"]); // sorted children
    Ok(())
}

#[test]
fn readdir_offset() -> Result<(), Errno> {
    let ops = build(
        FilesystemBuilder::new()
            .file("a", || "a")
            .file("b", || "b"),
    );
    let entries = ops.do_readdir(1, 2)?; // skip . and ..
    let names: Vec<&str> = entries.iter().map(|(_, _, n)| n.as_str()).collect();
    assert_eq!(names, vec!["a", "b"]);
    Ok(())
}

#[test]
fn readdir_types() -> Result<(), Errno> {
    let ops = build(
        FilesystemBuilder::new()
            .file("f", || "data")
            .dir("d", |_| {})
            .symlink("s", || "/x".to_owned()),
    );
    let entries = ops.do_readdir(1, 2)?; // skip . and ..
    let types: Vec<_> = entries.iter().map(|(_, ft, n)| (n.as_str(), *ft)).collect();
    assert!(types.contains(&("f", FileType::RegularFile)));
    assert!(types.contains(&("d", FileType::Directory)));
    assert!(types.contains(&("s", FileType::Symlink)));
    Ok(())
}

#[test]
fn readdir_not_a_dir() {
    let ops = build(FilesystemBuilder::new().file("f", || "data"));
    assert!(ops.do_readdir(2, 0).is_err());
}
