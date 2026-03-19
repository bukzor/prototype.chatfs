use std::time::SystemTime;

/// A file's content: data with optional metadata.
///
/// This is pure data — what you get when you read a file.
/// Construct via `File::from("content")` or `File::new("content")`,
/// then optionally chain `.mtime()` / `.mode()`.
#[derive(Debug, Clone)]
#[must_use]
pub struct File {
    pub data: String,
    pub mtime: Option<SystemTime>,
    pub mode: Option<u32>,
}

impl File {
    pub fn new(data: impl Into<String>) -> Self {
        Self {
            data: data.into(),
            mtime: None,
            mode: None,
        }
    }

    pub fn mtime(mut self, time: SystemTime) -> Self {
        self.mtime = Some(time);
        self
    }

    pub fn mode(mut self, mode: u32) -> Self {
        self.mode = Some(mode);
        self
    }
}

impl From<String> for File {
    fn from(s: String) -> Self {
        Self::new(s)
    }
}

impl From<&str> for File {
    fn from(s: &str) -> Self {
        Self::new(s)
    }
}
