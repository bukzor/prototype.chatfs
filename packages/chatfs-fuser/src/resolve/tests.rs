use std::collections::HashMap;
use std::sync::Arc;

use fuser::Errno;

use crate::path_segment::PathSegment;
use super::{Resolved, resolve_stale};

fn make_test_tree() -> PathSegment {
    PathSegment::Dir { read: Arc::new(|| {
        let mut children = HashMap::new();
        children.insert("README.md".to_owned(), PathSegment::File {
            read: Arc::new(|| "# hello\n".into()),
        });
        children.insert("link".to_owned(), PathSegment::Symlink {
            read: Arc::new(|| "/target".to_owned()),
        });
        children.insert("docs".to_owned(), PathSegment::Dir {
            read: Arc::new(|| {
                let mut inner = HashMap::new();
                inner.insert("api.md".to_owned(), PathSegment::File {
                    read: Arc::new(|| "# API\n".into()),
                });
                inner
            }),
        });
        children
    })}
}

fn assert_errno(actual: Errno, expected: Errno) {
    assert_eq!(i32::from(actual), i32::from(expected));
}

#[test]
fn resolve_root() -> Result<(), Errno> {
    let root = make_test_tree();
    let resolved = resolve_stale(&root, "/")?;
    match resolved {
        Resolved::Dir(children) => {
            assert!(children.contains_key("README.md"));
            assert!(children.contains_key("docs"));
            assert!(children.contains_key("link"));
        }
        _ => panic!("expected Dir"),
    }
    Ok(())
}

#[test]
fn resolve_file() -> Result<(), Errno> {
    let root = make_test_tree();
    let resolved = resolve_stale(&root, "/README.md")?;
    match resolved {
        Resolved::File(file) => assert_eq!(file.data, "# hello\n"),
        _ => panic!("expected File"),
    }
    Ok(())
}

#[test]
fn resolve_symlink() -> Result<(), Errno> {
    let root = make_test_tree();
    let resolved = resolve_stale(&root, "/link")?;
    match resolved {
        Resolved::Symlink(target) => assert_eq!(target, "/target"),
        _ => panic!("expected Symlink"),
    }
    Ok(())
}

#[test]
fn resolve_nested_file() -> Result<(), Errno> {
    let root = make_test_tree();
    let resolved = resolve_stale(&root, "/docs/api.md")?;
    match resolved {
        Resolved::File(file) => assert_eq!(file.data, "# API\n"),
        _ => panic!("expected File"),
    }
    Ok(())
}

#[test]
fn resolve_missing_returns_enoent() {
    let root = make_test_tree();
    let err = resolve_stale(&root, "/nonexistent").expect_err("should fail");
    assert_errno(err, Errno::ENOENT);
}

#[test]
fn resolve_through_file_returns_enotdir() {
    let root = make_test_tree();
    let err = resolve_stale(&root, "/README.md/child").expect_err("should fail");
    assert_errno(err, Errno::ENOTDIR);
}

#[test]
fn resolve_missing_nested_returns_enoent() {
    let root = make_test_tree();
    let err = resolve_stale(&root, "/docs/nonexistent").expect_err("should fail");
    assert_errno(err, Errno::ENOENT);
}
