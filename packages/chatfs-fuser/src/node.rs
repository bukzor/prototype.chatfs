use std::collections::HashMap;
use std::fmt;

use crate::File;

/// Internal tree node. Not exposed in the public API.
pub(crate) enum Node {
    Dir {
        children: HashMap<String, u64>,
    },
    File {
        read: Box<dyn Fn() -> File + Send + Sync>,
    },
    Symlink {
        target: Box<dyn Fn() -> String + Send + Sync>,
    },
}

impl fmt::Debug for Node {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Node::Dir { children } => f.debug_struct("Dir").field("children", children).finish(),
            Node::File { .. } => f.debug_struct("File").field("read", &"<closure>").finish(),
            Node::Symlink { .. } => {
                f.debug_struct("Symlink")
                    .field("target", &"<closure>")
                    .finish()
            }
        }
    }
}
