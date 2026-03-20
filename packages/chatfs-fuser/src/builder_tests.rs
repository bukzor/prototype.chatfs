use fuser::{Errno, INodeNo};

use crate::node_ops::NodeOps;
use crate::path_segment::Path;
use crate::resolve::{Resolved, resolve_stale};
use crate::FilesystemBuilder;

const ROOT: INodeNo = INodeNo(1);
const UID: u32 = 1000;
const GID: u32 = 1000;

/// Helper: build and return the root `Path`.
fn build(builder: FilesystemBuilder) -> Path {
    builder.build().expect("build failed").root
}

#[test]
fn build_empty() -> Result<(), Errno> {
    let root = build(FilesystemBuilder::new());
    let Resolved::Dir(children) = resolve_stale(&root, "/")? else {
        panic!("root is not a Dir");
    };
    assert!(children.is_empty());
    Ok(())
}

#[test]
fn build_single_file() -> Result<(), Errno> {
    let root = build(FilesystemBuilder::new().file("hello.txt", || "hi"));
    let Resolved::Dir(children) = resolve_stale(&root, "/")? else {
        panic!("root is not a Dir");
    };
    assert!(children.contains_key("hello.txt"));
    assert!(matches!(children["hello.txt"], Path::File { .. }));
    Ok(())
}

#[test]
fn build_inode_sequence() -> Result<(), Errno> {
    let ops = NodeOps::new(build(
        FilesystemBuilder::new()
            .file("a", || "a")
            .file("b", || "b")
            .file("c", || "c"),
    ));
    // Inodes assigned lazily in lookup order
    let (a, _) = ops.do_lookup(ROOT, "a", UID, GID)?;
    let (b, _) = ops.do_lookup(ROOT, "b", UID, GID)?;
    let (c, _) = ops.do_lookup(ROOT, "c", UID, GID)?;
    assert_eq!(a.ino, INodeNo(2));
    assert_eq!(b.ino, INodeNo(3));
    assert_eq!(c.ino, INodeNo(4));
    Ok(())
}

#[test]
fn build_nested_dir() -> Result<(), Errno> {
    let root = build(FilesystemBuilder::new().dir("d", |d| {
        d.file("f", || "content");
    }));
    let Resolved::File(file) = resolve_stale(&root, "/d/f")? else {
        panic!("expected File");
    };
    assert_eq!(file.data, "content");
    Ok(())
}

#[test]
fn build_symlink() -> Result<(), Errno> {
    let root = build(FilesystemBuilder::new().symlink("link", || "/target".to_owned()));
    let Resolved::Symlink(target) = resolve_stale(&root, "/link")? else {
        panic!("expected Symlink");
    };
    assert_eq!(target, "/target");
    Ok(())
}

#[test]
fn build_wrap_in_path() -> Result<(), Errno> {
    let root = build(FilesystemBuilder::new().dir("a/b/c", |d| {
        d.file("f", || "deep");
    }));

    // Verify nested structure
    let Resolved::Dir(root_children) = resolve_stale(&root, "/")? else {
        panic!("root is not a Dir");
    };
    assert!(root_children.contains_key("a"));
    assert!(!root_children.contains_key("b"));
    assert!(!root_children.contains_key("c"));

    // Traverse a -> b -> c -> f
    let Resolved::File(file) = resolve_stale(&root, "/a/b/c/f")? else {
        panic!("expected File at /a/b/c/f");
    };
    assert_eq!(file.data, "deep");
    Ok(())
}

#[test]
fn build_wrap_in_path_single() -> Result<(), Errno> {
    let root = build(FilesystemBuilder::new().dir("x", |d| {
        d.file("f", || "content");
    }));
    let Resolved::Dir(children) = resolve_stale(&root, "/")? else {
        panic!("root is not a Dir");
    };
    assert!(children.contains_key("x"));
    Ok(())
}

#[test]
fn build_dir_each() -> Result<(), Errno> {
    let root = build(FilesystemBuilder::new().dir_each(
        "pids",
        || vec!["1".to_owned(), "42".to_owned()],
        |pid, d| {
            let pid_clone = pid.clone();
            d.file("status", move || format!("Pid: {pid_clone}"));
        },
    ));

    let Resolved::Dir(pid_children) = resolve_stale(&root, "/pids")? else {
        panic!("pids is not a Dir");
    };
    assert!(pid_children.contains_key("1"));
    assert!(pid_children.contains_key("42"));

    let Resolved::File(file) = resolve_stale(&root, "/pids/1/status")? else {
        panic!("expected File");
    };
    assert_eq!(file.data, "Pid: 1");
    Ok(())
}

#[test]
fn build_dir_each_root_merge() -> Result<(), Errno> {
    let root = build(FilesystemBuilder::new().dir_each(
        "/",
        || vec!["x".to_owned(), "y".to_owned()],
        |_name, d| {
            d.file("f", || "content");
        },
    ));

    let Resolved::Dir(children) = resolve_stale(&root, "/")? else {
        panic!("root is not a Dir");
    };
    // Merged into root, not in a subdirectory
    assert!(children.contains_key("x"));
    assert!(children.contains_key("y"));

    let Resolved::File(file) = resolve_stale(&root, "/x/f")? else {
        panic!("expected File");
    };
    assert_eq!(file.data, "content");
    Ok(())
}
