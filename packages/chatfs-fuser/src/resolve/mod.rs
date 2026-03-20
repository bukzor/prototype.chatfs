use fuser::Errno;

use crate::File;
use crate::path_segment::{DirEntries, Path};

/// Result of resolving a path to a leaf and reading it.
#[derive(Debug)]
pub(crate) enum Resolved {
    Dir(DirEntries),
    File(File),
    Symlink(String),
}

/// Resolve a path through a `Path` tree and read the leaf.
///
/// Walks each path segment from root, calling `read()` at each Dir to get
/// children. At the final segment, calls the leaf's `read()` and returns
/// the result. Stateless — every call re-evaluates from root.
///
/// # Errors
///
/// - `ENOENT` — a path segment is missing from a Dir's children.
/// - `ENOTDIR` — traversal attempted through a non-Dir.
pub(crate) fn resolve_stale(root: &Path, path: &str) -> Result<Resolved, Errno> {
    if path == "/" {
        return Ok(read_segment(root));
    }

    let parts: Vec<&str> = path.split('/').filter(|s| !s.is_empty()).collect();

    // Walk to the parent of the final segment, collecting children at each level.
    let mut current_children = match root {
        Path::Dir { read } => read(),
        _ => return Err(Errno::ENOTDIR),
    };

    for (i, &part) in parts.iter().enumerate() {
        let segment = current_children.shift_remove(part).ok_or(Errno::ENOENT)?;

        if i == parts.len() - 1 {
            // Final segment — read it
            return Ok(read_segment(&segment));
        }

        // Intermediate segment — must be a Dir, descend
        current_children = match &segment {
            Path::Dir { read } => read(),
            _ => return Err(Errno::ENOTDIR),
        };
    }

    // Empty path parts (shouldn't happen after filter, but be safe)
    Ok(read_segment(root))
}

fn read_segment(segment: &Path) -> Resolved {
    match segment {
        Path::Dir { read } => Resolved::Dir(read()),
        Path::File { read } => Resolved::File(read()),
        Path::Symlink { read } => Resolved::Symlink(read()),
    }
}

#[cfg(test)]
mod tests;
