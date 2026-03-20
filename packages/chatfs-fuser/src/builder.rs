use std::collections::HashMap;

use crate::node::Node;
use crate::{File, Filesystem, Result};

type ReadFn = Box<dyn Fn() -> File + Send + Sync>;

/// A tree entry before inode assignment.
enum BuilderEntry {
    File { read: ReadFn },
    Dir { entries: Vec<(String, BuilderEntry)> },
}

impl std::fmt::Debug for BuilderEntry {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            BuilderEntry::File { .. } => f.debug_struct("File").finish_non_exhaustive(),
            BuilderEntry::Dir { entries } => {
                let names: Vec<_> = entries.iter().map(|(n, _)| n.as_str()).collect();
                f.debug_struct("Dir").field("entries", &names).finish()
            }
        }
    }
}

/// Builds a filesystem tree from files, directories, and symlinks.
#[derive(Debug)]
#[must_use]
pub struct FilesystemBuilder {
    entries: Vec<(String, BuilderEntry)>,
}

/// Builds the contents of a single directory.
///
/// Same API as `FilesystemBuilder` minus `.build()`.
pub struct DirBuilder {
    entries: Vec<(String, BuilderEntry)>,
}

impl std::fmt::Debug for DirBuilder {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let names: Vec<_> = self.entries.iter().map(|(n, _)| n.as_str()).collect();
        f.debug_struct("DirBuilder")
            .field("entries", &names)
            .finish()
    }
}

impl Default for FilesystemBuilder {
    fn default() -> Self {
        Self::new()
    }
}

/// Assign inodes recursively, returning the inode for this entry.
fn flatten(
    entry: BuilderEntry,
    next_ino: &mut u64,
    nodes: &mut HashMap<u64, Node>,
) -> u64 {
    let ino = *next_ino;
    *next_ino += 1;
    match entry {
        BuilderEntry::File { read } => {
            nodes.insert(ino, Node::File { read });
        }
        BuilderEntry::Dir { entries } => {
            let mut children = HashMap::new();
            for (name, child) in entries {
                let child_ino = flatten(child, next_ino, nodes);
                children.insert(name, child_ino);
            }
            nodes.insert(ino, Node::Dir { children });
        }
    }
    ino
}

impl FilesystemBuilder {
    pub fn new() -> Self {
        Self {
            entries: Vec::new(),
        }
    }

    /// Add a file. The closure is called on each read.
    pub fn file<F, R>(mut self, name: &str, read: F) -> Self
    where
        F: Fn() -> R + Send + Sync + 'static,
        R: Into<File>,
    {
        self.entries.push((
            name.to_owned(),
            BuilderEntry::File {
                read: Box::new(move || read().into()),
            },
        ));
        self
    }

    /// Add a symlink. The closure produces the target path.
    pub fn symlink(self, _name: &str, _target: impl Fn() -> String) -> Self {
        todo!()
    }

    /// Add a directory with fixed structure.
    pub fn dir(mut self, name: &str, build: impl FnOnce(&mut DirBuilder)) -> Self {
        let mut dir = DirBuilder {
            entries: Vec::new(),
        };
        build(&mut dir);
        self.entries.push((
            name.to_owned(),
            BuilderEntry::Dir {
                entries: dir.entries,
            },
        ));
        self
    }

    /// Add a dynamic directory: entries listed by `list_fn`,
    /// subtree templated by `template_fn` for each entry.
    pub fn dir_each<L, T>(
        self,
        _name: &str,
        _list_fn: L,
        _template_fn: T,
    ) -> Self
    where
        L: Fn() -> Vec<String>,
        T: Fn(String, &mut DirBuilder),
    {
        todo!()
    }

    /// Consume the builder and produce a mountable `Filesystem`.
    ///
    /// # Errors
    ///
    /// Returns an error if the filesystem tree is invalid.
    pub fn build(self) -> Result<Filesystem> {
        let mut nodes: HashMap<u64, Node> = HashMap::new();
        let mut next_ino: u64 = 2; // root is 1

        let mut children = HashMap::new();
        for (name, entry) in self.entries {
            let ino = flatten(entry, &mut next_ino, &mut nodes);
            children.insert(name, ino);
        }

        nodes.insert(1, Node::Dir { children });

        Ok(Filesystem::new(nodes))
    }
}

impl DirBuilder {
    /// Add a file. The closure is called on each read.
    pub fn file<F, R>(&mut self, name: &str, read: F) -> &mut Self
    where
        F: Fn() -> R + Send + Sync + 'static,
        R: Into<File>,
    {
        self.entries.push((
            name.to_owned(),
            BuilderEntry::File {
                read: Box::new(move || read().into()),
            },
        ));
        self
    }

    /// Add a symlink.
    pub fn symlink(&mut self, _name: &str, _target: impl Fn() -> String) -> &mut Self {
        todo!()
    }

    /// Add a nested directory.
    pub fn dir(&mut self, name: &str, build: impl FnOnce(&mut DirBuilder)) -> &mut Self {
        let mut dir = DirBuilder {
            entries: Vec::new(),
        };
        build(&mut dir);
        self.entries.push((
            name.to_owned(),
            BuilderEntry::Dir {
                entries: dir.entries,
            },
        ));
        self
    }
}
