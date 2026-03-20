use std::collections::HashMap;

use crate::Result;
use crate::node::Node;

/// A built filesystem, ready to mount.
pub struct Filesystem {
    pub(crate) nodes: HashMap<u64, Node>,
}

impl std::fmt::Debug for Filesystem {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("Filesystem")
            .field("nodes", &self.nodes)
            .finish()
    }
}

impl Filesystem {
    pub(crate) fn new(nodes: HashMap<u64, Node>) -> Self {
        Self { nodes }
    }

    /// Mount at `path` and block until unmounted.
    ///
    /// # Errors
    ///
    /// Returns `Error::Mount` if the mountpoint is invalid or mounting fails.
    /// Returns `Error::Io` on underlying I/O failures.
    pub fn mount(self, _path: &str) -> Result<()> {
        todo!()
    }
}
