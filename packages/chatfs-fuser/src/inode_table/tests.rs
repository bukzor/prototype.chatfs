use super::InodeTable;

#[test]
fn root_is_ino_1() {
    let table = InodeTable::new();
    assert_eq!(table.path_of(1), Some("/"));
}

#[test]
fn ensure_ino_assigns_stable_inodes() {
    let mut table = InodeTable::new();
    let ino = table.ensure_ino("/orgs");
    assert_eq!(ino, 2);
    // Same path returns same inode
    assert_eq!(table.ensure_ino("/orgs"), 2);
}

#[test]
fn ensure_ino_increments() {
    let mut table = InodeTable::new();
    let a = table.ensure_ino("/a");
    let b = table.ensure_ino("/b");
    assert_eq!(a, 2);
    assert_eq!(b, 3);
}

#[test]
fn path_of_returns_none_for_unknown() {
    let table = InodeTable::new();
    assert_eq!(table.path_of(999), None);
}

#[test]
fn parent_ino_of_root_is_none() {
    let table = InodeTable::new();
    assert_eq!(table.parent_ino("/"), None);
}

#[test]
fn parent_ino_of_top_level_is_root() {
    let mut table = InodeTable::new();
    table.ensure_ino("/orgs");
    assert_eq!(table.parent_ino("/orgs"), Some(1));
}

#[test]
fn parent_ino_of_nested_path() {
    let mut table = InodeTable::new();
    table.ensure_ino("/orgs");
    table.ensure_ino("/orgs/personal");
    assert_eq!(table.parent_ino("/orgs/personal"), Some(2));
}

#[test]
fn parent_ino_returns_none_if_parent_not_yet_assigned() {
    let table = InodeTable::new();
    // Parent "/orgs" has no inode yet
    assert_eq!(table.parent_ino("/orgs/personal"), None);
}
