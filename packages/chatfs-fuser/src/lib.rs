mod builder;
mod content;
mod error;
mod filesystem;

pub use builder::{DirBuilder, FilesystemBuilder};
pub use content::{FileContent, IntoContentSource};
pub use error::{Error, Result};
pub use filesystem::Filesystem;

pub mod prelude {
    pub use crate::{
        DirBuilder, FileContent, Filesystem, FilesystemBuilder, IntoContentSource,
        Error, Result,
    };
}
