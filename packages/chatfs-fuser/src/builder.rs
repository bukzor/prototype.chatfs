use std::collections::HashMap;

use crate::node::Node;
use crate::{File, Filesystem, Result};

/// Builds a filesystem tree from files, directories, and symlinks.
#[derive(Debug)]
#[must_use]
pub struct FilesystemBuilder {
    entries: Vec<(String, Node)>,
}

/// Builds the contents of a single directory.
///
/// Same API as `FilesystemBuilder` minus `.build()`.
#[derive(Debug)]
pub struct DirBuilder {
    // TODO: entries
}

impl Default for FilesystemBuilder {
    fn default() -> Self {
        Self::new()
    }
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
            Node::File {
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
    pub fn dir(self, _name: &str, _build: impl FnOnce(&mut DirBuilder)) -> Self {
        todo!()
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
        for (name, node) in self.entries {
            let ino = next_ino;
            next_ino += 1;
            children.insert(name, ino);
            nodes.insert(ino, node);
        }

        nodes.insert(1, Node::Dir { children });

        Ok(Filesystem::new(nodes))
    }
}

impl DirBuilder {
    /// Add a file. The closure is called on each read.
    pub fn file<F, R>(&mut self, _name: &str, _read: F) -> &mut Self
    where
        F: Fn() -> R,
        R: Into<File>,
    {
        todo!()
    }

    /// Add a symlink.
    pub fn symlink(&mut self, _name: &str, _target: impl Fn() -> String) -> &mut Self {
        todo!()
    }

    /// Add a nested directory.
    pub fn dir(&mut self, _name: &str, _build: impl FnOnce(&mut DirBuilder)) -> &mut Self {
        todo!()
    }
}
