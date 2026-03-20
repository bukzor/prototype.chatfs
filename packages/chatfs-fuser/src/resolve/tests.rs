use std::collections::HashMap;

use fuser::Errno;

use crate::path_segment::PathSegment;
use super::{Resolved, resolve_and_read};

fn make_test_tree() -> PathSegment {
    PathSegment::Dir { read: Box::new(|| {
        let mut children = HashMap::new();
        children.insert("README.md".to_owned(), PathSegment::File {
            read: Box::new(|| "# hello\n".into()),
        });
        children.insert("link".to_owned(), PathSegment::Symlink {
            read: Box::new(|| "/target".to_owned()),
        });
        children.insert("docs".to_owned(), PathSegment::Dir {
            read: Box::new(|| {
                let mut inner = HashMap::new();
                inner.insert("api.md".to_owned(), PathSegment::File {
                    read: Box::new(|| "# API\n".into()),
                });
                inner
            }),
        });
        children
    })}
}

fn assert_errno(result: Result<Resolved, Errno>, expected: Errno) {
    let err = result.unwrap_err();
    assert_eq!(i32::from(err), i32::from(expected));
}

#[test]
fn resolve_root() {
    let root = make_test_tree();
    let resolved = resolve_and_read(&root, "/").unwrap();
    match resolved {
        Resolved::Dir(children) => {
            assert!(children.contains_key("README.md"));
            assert!(children.contains_key("docs"));
            assert!(children.contains_key("link"));
        }
        _ => panic!("expected Dir"),
    }
}

#[test]
fn resolve_file() {
    let root = make_test_tree();
    let resolved = resolve_and_read(&root, "/README.md").unwrap();
    match resolved {
        Resolved::File(file) => assert_eq!(file.data, "# hello\n"),
        _ => panic!("expected File"),
    }
}

#[test]
fn resolve_symlink() {
    let root = make_test_tree();
    let resolved = resolve_and_read(&root, "/link").unwrap();
    match resolved {
        Resolved::Symlink(target) => assert_eq!(target, "/target"),
        _ => panic!("expected Symlink"),
    }
}

#[test]
fn resolve_nested_file() {
    let root = make_test_tree();
    let resolved = resolve_and_read(&root, "/docs/api.md").unwrap();
    match resolved {
        Resolved::File(file) => assert_eq!(file.data, "# API\n"),
        _ => panic!("expected File"),
    }
}

#[test]
fn resolve_missing_returns_enoent() {
    let root = make_test_tree();
    assert_errno(resolve_and_read(&root, "/nonexistent"), Errno::ENOENT);
}

#[test]
fn resolve_through_file_returns_enotdir() {
    let root = make_test_tree();
    assert_errno(resolve_and_read(&root, "/README.md/child"), Errno::ENOTDIR);
}

#[test]
fn resolve_missing_nested_returns_enoent() {
    let root = make_test_tree();
    assert_errno(resolve_and_read(&root, "/docs/nonexistent"), Errno::ENOENT);
}
