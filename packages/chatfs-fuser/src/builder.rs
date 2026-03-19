use crate::{Filesystem, IntoContentSource, Result};

/// Builds a filesystem tree from files, directories, and symlinks.
pub struct FilesystemBuilder {
    // TODO: tree representation
}

/// Builds the contents of a single directory.
///
/// Same API as `FilesystemBuilder` minus `.build()`.
pub struct DirBuilder {
    // TODO: entries
}

impl FilesystemBuilder {
    pub fn new() -> Self {
        todo!()
    }

    /// Add a read-only file with content from any `IntoContentSource`.
    pub fn file(self, _name: &str, _content: impl IntoContentSource) -> Self {
        todo!()
    }

    /// Add a symlink whose target is produced by a closure.
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
        T: Fn(&str, &mut DirBuilder),
    {
        todo!()
    }

    /// Consume the builder and produce a mountable `Filesystem`.
    pub fn build(self) -> Result<Filesystem> {
        todo!()
    }
}

impl DirBuilder {
    /// Add a read-only file.
    pub fn file(&mut self, _name: &str, _content: impl IntoContentSource) -> &mut Self {
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
