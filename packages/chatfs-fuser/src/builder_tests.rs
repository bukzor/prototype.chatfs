use crate::node::Node;
use crate::FilesystemBuilder;

/// Helper: build and return the node map.
fn build(builder: FilesystemBuilder) -> std::collections::HashMap<u64, Node> {
    builder.build().expect("build failed").nodes
}

#[test]
fn build_empty() {
    let nodes = build(FilesystemBuilder::new());
    assert_eq!(nodes.len(), 1); // root only
    let Node::Dir { children } = &nodes[&1] else {
        panic!("root is not a Dir");
    };
    assert!(children.is_empty());
}

#[test]
fn build_single_file() {
    let nodes = build(FilesystemBuilder::new().file("hello.txt", || "hi"));
    assert_eq!(nodes.len(), 2); // root + file
    let Node::Dir { children } = &nodes[&1] else {
        panic!("root is not a Dir");
    };
    assert_eq!(children["hello.txt"], 2);
    assert!(matches!(nodes[&2], Node::File { .. }));
}

#[test]
fn build_inode_sequence() {
    let nodes = build(
        FilesystemBuilder::new()
            .file("a", || "a")
            .file("b", || "b")
            .file("c", || "c"),
    );
    assert_eq!(nodes.len(), 4); // root + 3 files
    let Node::Dir { children } = &nodes[&1] else {
        panic!("root is not a Dir");
    };
    assert_eq!(children["a"], 2);
    assert_eq!(children["b"], 3);
    assert_eq!(children["c"], 4);
}

#[test]
fn build_nested_dir() {
    let nodes = build(FilesystemBuilder::new().dir("d", |d| {
        d.file("f", || "content");
    }));
    assert_eq!(nodes.len(), 3); // root + dir + file
    let Node::Dir { children: root_children } = &nodes[&1] else {
        panic!("root is not a Dir");
    };
    let dir_ino = root_children["d"];
    let Node::Dir { children: dir_children } = &nodes[&dir_ino] else {
        panic!("d is not a Dir");
    };
    let file_ino = dir_children["f"];
    assert!(matches!(nodes[&file_ino], Node::File { .. }));
}

#[test]
fn build_symlink() {
    let nodes = build(FilesystemBuilder::new().symlink("link", || "/target".to_owned()));
    assert_eq!(nodes.len(), 2);
    assert!(matches!(nodes[&2], Node::Symlink { .. }));
}

#[test]
fn build_wrap_in_path() {
    let nodes = build(FilesystemBuilder::new().dir("a/b/c", |d| {
        d.file("f", || "deep");
    }));
    // root + a + b + c + f = 5
    assert_eq!(nodes.len(), 5);

    let Node::Dir { children } = &nodes[&1] else {
        panic!("root is not a Dir");
    };
    assert!(children.contains_key("a"));
    assert!(!children.contains_key("b"));
    assert!(!children.contains_key("c"));

    // Traverse a -> b -> c -> f
    let a_ino = children["a"];
    let Node::Dir { children: a_children } = &nodes[&a_ino] else {
        panic!("a is not a Dir");
    };
    let b_ino = a_children["b"];
    let Node::Dir { children: b_children } = &nodes[&b_ino] else {
        panic!("b is not a Dir");
    };
    let c_ino = b_children["c"];
    let Node::Dir { children: c_children } = &nodes[&c_ino] else {
        panic!("c is not a Dir");
    };
    assert!(c_children.contains_key("f"));
}

#[test]
fn build_wrap_in_path_single() {
    let nodes = build(FilesystemBuilder::new().dir("x", |d| {
        d.file("f", || "content");
    }));
    assert_eq!(nodes.len(), 3); // root + x + f
    let Node::Dir { children } = &nodes[&1] else {
        panic!("root is not a Dir");
    };
    assert!(children.contains_key("x"));
}

#[test]
fn build_dir_each() {
    let nodes = build(FilesystemBuilder::new().dir_each(
        "pids",
        || vec!["1".to_owned(), "42".to_owned()],
        |pid, d| {
            let pid_clone = pid.clone();
            d.file("status", move || format!("Pid: {pid_clone}"));
        },
    ));
    // root + pids + (1 + status) + (42 + status) = 6
    assert_eq!(nodes.len(), 6);

    let Node::Dir { children } = &nodes[&1] else {
        panic!("root is not a Dir");
    };
    let pids_ino = children["pids"];
    let Node::Dir { children: pid_children } = &nodes[&pids_ino] else {
        panic!("pids is not a Dir");
    };
    assert!(pid_children.contains_key("1"));
    assert!(pid_children.contains_key("42"));
}

#[test]
fn build_dir_each_root_merge() {
    let nodes = build(FilesystemBuilder::new().dir_each(
        "/",
        || vec!["x".to_owned(), "y".to_owned()],
        |_name, d| {
            d.file("f", || "content");
        },
    ));
    // root + (x + f) + (y + f) = 5
    assert_eq!(nodes.len(), 5);

    let Node::Dir { children } = &nodes[&1] else {
        panic!("root is not a Dir");
    };
    // Merged into root, not in a subdirectory
    assert!(children.contains_key("x"));
    assert!(children.contains_key("y"));
}
