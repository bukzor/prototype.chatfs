// Stubs — bodies will be filled in as we implement.
#![allow(clippy::todo)]
// Structs will get fields as we implement.
#![allow(clippy::empty_structs_with_brackets)]

mod builder;
mod error;
mod file;
mod filesystem;
mod node;

pub use builder::{DirBuilder, FilesystemBuilder};
pub use error::{Error, Result};
pub use file::File;
pub use filesystem::Filesystem;

pub mod prelude {
    pub use crate::{DirBuilder, File, Filesystem, FilesystemBuilder, Error, Result};
}
