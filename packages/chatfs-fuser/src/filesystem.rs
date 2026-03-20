use crate::Result;
use crate::fuse_impl::FuseFs;
use crate::node_ops::NodeOps;
use crate::path_segment::Path;

/// A built filesystem, ready to mount.
pub struct Filesystem {
    pub root: Path,
}

impl std::fmt::Debug for Filesystem {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("Filesystem")
            .field("root", &self.root)
            .finish()
    }
}

impl Filesystem {
    #[must_use]
    pub fn new(root: Path) -> Self {
        Self { root }
    }

    /// Mount at `path` and block until unmounted.
    ///
    /// # Errors
    ///
    /// Returns `Error::Mount` if the mountpoint is invalid or mounting fails.
    /// Returns `Error::Io` on underlying I/O failures.
    pub fn mount(self, path: impl AsRef<std::path::Path>) -> Result<()> {
        let path = path.as_ref();
        std::fs::create_dir_all(path)?;
        let ops = NodeOps::new(self.root);
        let fuse_fs = FuseFs::new(ops);
        fuser::mount2(fuse_fs, path, &fuser::Config::default())?;
        Ok(())
    }
}
