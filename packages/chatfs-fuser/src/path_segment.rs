use std::fmt;
use std::sync::Arc;

use indexmap::IndexMap;

use crate::File;

/// Ordered map of directory entry names to their `Path` definitions.
///
/// Preserves insertion order — `readdir` returns entries in the order
/// the caller's closure provides them.
pub type DirEntries = IndexMap<String, Path>;

pub type ReadFileFn = Arc<dyn Fn() -> File + Send + Sync>;
pub type ReadDirFn = Arc<dyn Fn() -> DirEntries + Send + Sync>;
pub type ReadLinkFn = Arc<dyn Fn() -> String + Send + Sync>;

/// What a path name resolves to — the runtime tree definition.
///
/// All variants are callback-driven. A "static" directory is just one
/// whose `read` returns a fixed map. The framework doesn't distinguish.
///
/// Clone is cheap — inner callbacks are `Arc`-wrapped.
pub enum Path {
    Dir { read: ReadDirFn },
    File { read: ReadFileFn },
    Symlink { read: ReadLinkFn },
}

impl Clone for Path {
    fn clone(&self) -> Self {
        match self {
            Path::Dir { read } => Path::Dir { read: Arc::clone(read) },
            Path::File { read } => Path::File { read: Arc::clone(read) },
            Path::Symlink { read } => Path::Symlink { read: Arc::clone(read) },
        }
    }
}

impl fmt::Debug for Path {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Path::Dir { .. } => f.debug_struct("Dir").finish_non_exhaustive(),
            Path::File { .. } => f.debug_struct("File").finish_non_exhaustive(),
            Path::Symlink { .. } => f.debug_struct("Symlink").finish_non_exhaustive(),
        }
    }
}
