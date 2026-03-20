use std::collections::HashMap;
use std::path::Path;

use crate::Result;
use crate::fuse_impl::FuseFs;
use crate::node::Node;
use crate::node_ops::NodeOps;

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
    pub fn mount(self, path: impl AsRef<Path>) -> Result<()> {
        let path = path.as_ref();
        std::fs::create_dir_all(path)?;
        let ops = NodeOps::new(self.nodes);
        let fuse_fs = FuseFs::new(ops);
        fuser::mount2(fuse_fs, path, &fuser::Config::default())?;
        Ok(())
    }
}
