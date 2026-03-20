use std::collections::HashMap;
use std::fmt;
use std::sync::Arc;

use crate::File;

pub type ReadFileFn = Arc<dyn Fn() -> File + Send + Sync>;
pub type ReadDirFn = Arc<dyn Fn() -> HashMap<String, PathSegment> + Send + Sync>;
pub type ReadLinkFn = Arc<dyn Fn() -> String + Send + Sync>;

/// What a path name resolves to — the runtime tree definition.
///
/// All variants are callback-driven. A "static" directory is just one
/// whose `read` returns a fixed map. The framework doesn't distinguish.
///
/// Clone is cheap — inner callbacks are `Arc`-wrapped.
pub enum PathSegment {
    Dir { read: ReadDirFn },
    File { read: ReadFileFn },
    Symlink { read: ReadLinkFn },
}

impl Clone for PathSegment {
    fn clone(&self) -> Self {
        match self {
            PathSegment::Dir { read } => PathSegment::Dir { read: Arc::clone(read) },
            PathSegment::File { read } => PathSegment::File { read: Arc::clone(read) },
            PathSegment::Symlink { read } => PathSegment::Symlink { read: Arc::clone(read) },
        }
    }
}

impl fmt::Debug for PathSegment {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            PathSegment::Dir { .. } => f.debug_struct("Dir").finish_non_exhaustive(),
            PathSegment::File { .. } => f.debug_struct("File").finish_non_exhaustive(),
            PathSegment::Symlink { .. } => f.debug_struct("Symlink").finish_non_exhaustive(),
        }
    }
}
