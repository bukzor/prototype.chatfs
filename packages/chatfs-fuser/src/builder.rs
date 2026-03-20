use std::sync::Arc;

use crate::path_segment::{DirEntries, Path};
use crate::{File, Filesystem, Result};

type ReadFn = Box<dyn Fn() -> File + Send + Sync>;
type TargetFn = Box<dyn Fn() -> String + Send + Sync>;

/// A tree entry before conversion to `Path`.
enum BuilderEntry {
    File { read: ReadFn },
    Dir { entries: Vec<(String, BuilderEntry)> },
    Symlink { target: TargetFn },
}

impl std::fmt::Debug for BuilderEntry {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            BuilderEntry::File { .. } => f.debug_struct("File").finish_non_exhaustive(),
            BuilderEntry::Dir { entries } => {
                let names: Vec<_> = entries.iter().map(|(n, _)| n.as_str()).collect();
                f.debug_struct("Dir").field("entries", &names).finish()
            }
            BuilderEntry::Symlink { .. } => {
                f.debug_struct("Symlink").finish_non_exhaustive()
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

/// Wrap entries in nested directories for a slash-separated path.
/// e.g. `wrap_in_path("sys/vm", entries)` → `("sys", Dir{[("vm", Dir{entries})]})`
fn wrap_in_path(path: &str, entries: Vec<(String, BuilderEntry)>) -> (String, BuilderEntry) {
    let parts: Vec<&str> = path.split('/').filter(|s| !s.is_empty()).collect();
    assert!(!parts.is_empty(), "dir() name must not be empty");

    // Build from inside out: leaf dir contains the entries,
    // each outer segment wraps the previous in a new dir.
    let mut entry = BuilderEntry::Dir { entries };
    for &segment in parts[1..].iter().rev() {
        entry = BuilderEntry::Dir {
            entries: vec![(segment.to_owned(), entry)],
        };
    }
    (parts[0].to_owned(), entry)
}

/// Convert a `BuilderEntry` tree into a `Path` tree.
///
/// Static dirs become `Path::Dir` whose `read` closure returns a
/// cloned map of the children (Clone is cheap — Arc refcount bumps).
fn convert(entry: BuilderEntry) -> Path {
    match entry {
        BuilderEntry::File { read } => Path::File { read: Arc::from(read) },
        BuilderEntry::Symlink { target } => Path::Symlink { read: Arc::from(target) },
        BuilderEntry::Dir { entries } => {
            let children: DirEntries = entries
                .into_iter()
                .map(|(name, child)| (name, convert(child)))
                .collect();
            Path::Dir {
                read: Arc::new(move || children.clone()),
            }
        }
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
            BuilderEntry::File {
                read: Box::new(move || read().into()),
            },
        ));
        self
    }

    /// Add a symlink. The closure produces the target path.
    pub fn symlink(mut self, name: &str, target: impl Fn() -> String + Send + Sync + 'static) -> Self {
        self.entries.push((
            name.to_owned(),
            BuilderEntry::Symlink {
                target: Box::new(target),
            },
        ));
        self
    }

    /// Add a directory with fixed structure.
    ///
    /// `name` may contain `/` to create intermediate directories,
    /// e.g. `dir("sys/vm", ...)` creates `sys/` containing `vm/`.
    pub fn dir(mut self, name: &str, build: impl FnOnce(&mut DirBuilder)) -> Self {
        let mut dir = DirBuilder {
            entries: Vec::new(),
        };
        build(&mut dir);
        let entry = wrap_in_path(name, dir.entries);
        self.entries.push(entry);
        self
    }

    /// Expand `list_fn` items into directories via `template_fn`.
    ///
    /// `list_fn` is called once at build time to get entry names.
    /// `template_fn` is called once per entry at build time to build its subtree.
    ///
    /// If `name` is `"/"`, entries are merged into the current directory level.
    /// Otherwise, entries are placed inside a new directory with the given name.
    pub fn dir_each<L, T>(mut self, name: &str, list_fn: L, template_fn: T) -> Self
    where
        L: Fn() -> Vec<String>,
        T: Fn(String, &mut DirBuilder),
    {
        let items = list_fn();
        if name == "/" {
            for item in items {
                self = self.dir(&item, |d| template_fn(item.clone(), d));
            }
        } else {
            self = self.dir(name, |d| {
                for item in items {
                    d.dir(&item, |inner| template_fn(item.clone(), inner));
                }
            });
        }
        self
    }

    /// Consume the builder and produce a mountable `Filesystem`.
    ///
    /// # Errors
    ///
    /// Returns an error if the filesystem tree is invalid.
    pub fn build(self) -> Result<Filesystem> {
        let root = convert(BuilderEntry::Dir {
            entries: self.entries,
        });
        Ok(Filesystem::new(root))
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
    pub fn symlink(&mut self, name: &str, target: impl Fn() -> String + Send + Sync + 'static) -> &mut Self {
        self.entries.push((
            name.to_owned(),
            BuilderEntry::Symlink {
                target: Box::new(target),
            },
        ));
        self
    }

    /// Add a nested directory (supports slash-separated paths).
    pub fn dir(&mut self, name: &str, build: impl FnOnce(&mut DirBuilder)) -> &mut Self {
        let mut dir = DirBuilder {
            entries: Vec::new(),
        };
        build(&mut dir);
        let entry = wrap_in_path(name, dir.entries);
        self.entries.push(entry);
        self
    }
}
