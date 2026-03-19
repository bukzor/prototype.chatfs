use crate::Result;

/// A built filesystem, ready to mount.
#[derive(Debug)]
pub struct Filesystem {
    // TODO: tree + fuser session state
}

impl Filesystem {
    /// Mount at `path` and block until unmounted.
    ///
    /// # Errors
    ///
    /// Returns `Error::Mount` if the mountpoint is invalid or mounting fails.
    /// Returns `Error::Io` on underlying I/O failures.
    pub fn mount(&self, _path: &str) -> Result<()> {
        todo!()
    }
}
