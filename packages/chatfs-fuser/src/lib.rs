mod builder;
mod error;
mod file;
mod filesystem;
mod fuse_impl;
mod inode_table;
mod node_ops;
mod path_segment;
mod resolve;

#[cfg(test)]
mod builder_tests;
#[cfg(test)]
mod node_ops_tests;

pub use builder::{DirBuilder, FilesystemBuilder};
pub use error::{Error, Result};
pub use file::File;
pub use filesystem::Filesystem;
pub use path_segment::{DirEntries, Path, ReadDirFn, ReadFileFn, ReadLinkFn};

pub mod prelude {
    pub use crate::{DirBuilder, DirEntries, File, Filesystem, FilesystemBuilder, Error, Path, Result};
}
