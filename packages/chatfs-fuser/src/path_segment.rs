use std::collections::HashMap;
use std::fmt;

use crate::File;

type ReadFileFn = Box<dyn Fn() -> File + Send + Sync>;
type ReadDirFn = Box<dyn Fn() -> HashMap<String, PathSegment> + Send + Sync>;
type ReadLinkFn = Box<dyn Fn() -> String + Send + Sync>;

/// What a path name resolves to — the runtime tree definition.
///
/// All variants are callback-driven. A "static" directory is just one
/// whose `read` returns a fixed map. The framework doesn't distinguish.
#[cfg_attr(not(test), expect(dead_code, reason = "wired up when NodeOps switches to PathSegment"))]
pub(crate) enum PathSegment {
    Dir { read: ReadDirFn },
    File { read: ReadFileFn },
    Symlink { read: ReadLinkFn },
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
