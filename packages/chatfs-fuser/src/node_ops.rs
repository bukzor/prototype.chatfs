use std::sync::Mutex;
use std::time::SystemTime;

use fuser::{Errno, FileAttr, FileType, Generation, INodeNo};

use crate::inode_table::InodeTable;
use crate::path_segment::Path;
use crate::resolve::{Resolved, resolve_stale};

/// Pure node-tree operations — testable without FUSE.
pub(crate) struct NodeOps {
    root: Path,
    table: Mutex<InodeTable>,
}

impl NodeOps {
    pub(crate) fn new(root: Path) -> Self {
        Self {
            root,
            table: Mutex::new(InodeTable::new()),
        }
    }

    pub(crate) fn do_lookup(
        &self,
        parent_ino: INodeNo,
        name: &str,
        uid: u32,
        gid: u32,
    ) -> Result<(FileAttr, Generation), Errno> {
        let table = self.table.lock().expect("inode table lock poisoned");
        let parent_path = table.path_of(parent_ino).ok_or(Errno::ENOENT)?;
        let child_path = if parent_path == "/" {
            format!("/{name}")
        } else {
            format!("{parent_path}/{name}")
        };
        drop(table);

        // Resolve to verify the path exists and get its type
        let resolved = resolve_stale(&self.root, &child_path)?;

        let mut table = self.table.lock().expect("inode table lock poisoned");
        let child_ino = table.ensure_ino(&child_path);
        let attr = Self::resolved_attr(child_ino, &resolved, uid, gid);
        Ok((attr, Generation(0)))
    }

    pub(crate) fn do_getattr(&self, ino: INodeNo, uid: u32, gid: u32) -> Result<FileAttr, Errno> {
        let table = self.table.lock().expect("inode table lock poisoned");
        let path = table.path_of(ino).ok_or(Errno::ENOENT)?.to_owned();
        drop(table);

        let resolved = self.resolve(&path)?;
        Ok(Self::resolved_attr(ino, &resolved, uid, gid))
    }

    pub(crate) fn do_read(&self, ino: INodeNo, offset: u64, size: u32) -> Result<Vec<u8>, Errno> {
        let table = self.table.lock().expect("inode table lock poisoned");
        let path = table.path_of(ino).ok_or(Errno::ENOENT)?.to_owned();
        drop(table);

        let resolved = self.resolve(&path)?;
        let Resolved::File(file) = resolved else {
            return Err(Errno::ENOENT);
        };

        let data = file.data.as_bytes();
        let offset = usize::try_from(offset).unwrap_or(usize::MAX);
        if offset >= data.len() {
            Ok(Vec::new())
        } else {
            let size = usize::try_from(size).unwrap_or(usize::MAX);
            let end = offset.saturating_add(size).min(data.len());
            Ok(data[offset..end].to_vec())
        }
    }

    pub(crate) fn do_readlink(&self, ino: INodeNo) -> Result<Vec<u8>, Errno> {
        let table = self.table.lock().expect("inode table lock poisoned");
        let path = table.path_of(ino).ok_or(Errno::ENOENT)?.to_owned();
        drop(table);

        let resolved = self.resolve(&path)?;
        let Resolved::Symlink(target) = resolved else {
            return Err(Errno::ENOENT);
        };
        Ok(target.into_bytes())
    }

    pub(crate) fn do_readdir(
        &self,
        ino: INodeNo,
        offset: u64,
    ) -> Result<Vec<(INodeNo, FileType, String)>, Errno> {
        let table = self.table.lock().expect("inode table lock poisoned");
        let path = table.path_of(ino).ok_or(Errno::ENOENT)?.to_owned();
        let parent_ino = table.parent_ino(&path).unwrap_or(ino);
        drop(table);

        let resolved = self.resolve(&path)?;
        let Resolved::Dir(children) = resolved else {
            return Err(Errno::ENOTDIR);
        };

        let mut entries: Vec<(INodeNo, FileType, String)> = Vec::new();
        entries.push((ino, FileType::Directory, ".".to_owned()));
        entries.push((parent_ino, FileType::Directory, "..".to_owned()));

        let mut table = self.table.lock().expect("inode table lock poisoned");
        for (name, segment) in &children {
            let child_path = if path == "/" {
                format!("/{name}")
            } else {
                format!("{path}/{name}")
            };
            let child_ino = table.ensure_ino(&child_path);
            let file_type = match segment {
                Path::Dir { .. } => FileType::Directory,
                Path::File { .. } => FileType::RegularFile,
                Path::Symlink { .. } => FileType::Symlink,
            };
            entries.push((child_ino, file_type, name.clone()));
        }

        let skip = usize::try_from(offset).unwrap_or(usize::MAX);
        Ok(entries.into_iter().skip(skip).collect())
    }

    /// Resolve a path that is known to be in the inode table.
    /// Any resolution failure means the inode is stale → ESTALE.
    fn resolve(&self, path: &str) -> Result<Resolved, Errno> {
        resolve_stale(&self.root, path).map_err(|_| Errno::ESTALE)
    }

    fn resolved_attr(ino: INodeNo, resolved: &Resolved, uid: u32, gid: u32) -> FileAttr {
        match resolved {
            Resolved::Dir(_) => FileAttr {
                ino,
                size: 0,
                blocks: 0,
                atime: SystemTime::UNIX_EPOCH,
                mtime: SystemTime::UNIX_EPOCH,
                ctime: SystemTime::UNIX_EPOCH,
                crtime: SystemTime::UNIX_EPOCH,
                kind: FileType::Directory,
                perm: 0o555,
                nlink: 2,
                uid,
                gid,
                rdev: 0,
                blksize: 512,
                flags: 0,
            },
            Resolved::File(file) => {
                let size = file.data.len() as u64;
                let mtime = file.mtime.unwrap_or(SystemTime::UNIX_EPOCH);
                #[expect(clippy::cast_possible_truncation, reason = "mode fits in u16 by construction")]
                let perm = file.mode.map_or(0o444, |m| m as u16);
                FileAttr {
                    ino,
                    size,
                    blocks: size.div_ceil(512),
                    atime: mtime,
                    mtime,
                    ctime: mtime,
                    crtime: mtime,
                    kind: FileType::RegularFile,
                    perm,
                    nlink: 1,
                    uid,
                    gid,
                    rdev: 0,
                    blksize: 512,
                    flags: 0,
                }
            }
            Resolved::Symlink(target) => FileAttr {
                ino,
                size: target.len() as u64,
                blocks: 0,
                atime: SystemTime::UNIX_EPOCH,
                mtime: SystemTime::UNIX_EPOCH,
                ctime: SystemTime::UNIX_EPOCH,
                crtime: SystemTime::UNIX_EPOCH,
                kind: FileType::Symlink,
                perm: 0o777,
                nlink: 1,
                uid,
                gid,
                rdev: 0,
                blksize: 512,
                flags: 0,
            },
        }
    }
}
