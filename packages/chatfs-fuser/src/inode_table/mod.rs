use std::collections::HashMap;

use fuser::INodeNo;

/// Bidirectional path ↔ inode mapping with lazy allocation.
///
/// Inodes are assigned on first encounter (lookup/readdir) and stable
/// thereafter. The table is append-only — see inode-lifecycle policy.
pub(crate) struct InodeTable {
    path_to_ino: HashMap<String, INodeNo>,
    ino_to_path: HashMap<INodeNo, String>,
    next_ino: u64,
}

impl InodeTable {
    /// Create a new table with root (ino=1) pre-registered.
    pub(crate) fn new() -> Self {
        let root = INodeNo(1);
        let mut table = Self {
            path_to_ino: HashMap::new(),
            ino_to_path: HashMap::new(),
            next_ino: 2,
        };
        table.path_to_ino.insert("/".to_owned(), root);
        table.ino_to_path.insert(root, "/".to_owned());
        table
    }

    /// Get or assign an inode for `path`.
    pub(crate) fn ensure_ino(&mut self, path: &str) -> INodeNo {
        if let Some(&ino) = self.path_to_ino.get(path) {
            return ino;
        }
        let ino = INodeNo(self.next_ino);
        self.next_ino += 1;
        self.path_to_ino.insert(path.to_owned(), ino);
        self.ino_to_path.insert(ino, path.to_owned());
        ino
    }

    /// Look up the path for an inode.
    pub(crate) fn path_of(&self, ino: INodeNo) -> Option<&str> {
        self.ino_to_path.get(&ino).map(String::as_str)
    }

    /// Derive the parent inode from a path. Returns None for root.
    pub(crate) fn parent_ino(&self, path: &str) -> Option<INodeNo> {
        if path == "/" {
            return None;
        }
        let parent = match path.rfind('/') {
            Some(0) => "/",
            Some(i) => &path[..i],
            None => return None,
        };
        self.path_to_ino.get(parent).copied()
    }
}

impl std::fmt::Debug for InodeTable {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("InodeTable")
            .field("count", &self.ino_to_path.len())
            .field("next_ino", &self.next_ino)
            .finish_non_exhaustive()
    }
}

#[cfg(test)]
mod tests;
