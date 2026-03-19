use std::time::SystemTime;

/// File content with optional metadata.
///
/// Return this from a file callback to attach mtime, mode, etc.
/// Plain `String` or `&str` auto-converts via `IntoContentSource`.
pub struct FileContent {
    pub data: String,
    pub mtime: Option<SystemTime>,
    pub mode: Option<u32>,
}

impl FileContent {
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

/// Trait for things that can serve as file content sources.
///
/// Implemented for:
/// - `&str` / `String` — static content
/// - `Fn() -> String` — dynamic content, default metadata
/// - `Fn() -> FileContent` — dynamic content with metadata
pub trait IntoContentSource {
    fn read(&self) -> FileContent;
}

impl IntoContentSource for &str {
    fn read(&self) -> FileContent {
        FileContent::new(*self)
    }
}

impl IntoContentSource for String {
    fn read(&self) -> FileContent {
        FileContent::new(self.clone())
    }
}

impl<F: Fn() -> String> IntoContentSource for F {
    fn read(&self) -> FileContent {
        FileContent::new(self())
    }
}

// Note: Fn() -> FileContent conflicts with Fn() -> String in generic impls.
// Will need a newtype or different approach at impl time.
