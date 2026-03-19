use crate::Result;

/// A built filesystem, ready to mount.
pub struct Filesystem {
    // TODO: tree + fuser session state
}

impl Filesystem {
    /// Mount at `path` and block until unmounted.
    pub fn mount(&self, _path: &str) -> Result<()> {
        todo!()
    }
}
