use std::collections::HashMap;
use std::time::SystemTime;

use fuser::{Errno, FileAttr, FileType, Generation, INodeNo};

use crate::node::Node;

/// Pure node-tree operations — testable without FUSE.
pub(crate) struct NodeOps {
    nodes: HashMap<u64, Node>,
}

impl NodeOps {
    pub(crate) fn new(nodes: HashMap<u64, Node>) -> Self {
        Self { nodes }
    }

    pub(crate) fn do_lookup(
        &self,
        parent_ino: u64,
        name: &str,
        uid: u32,
        gid: u32,
    ) -> Result<(FileAttr, Generation), Errno> {
        let Node::Dir { children } = self.nodes.get(&parent_ino).ok_or(Errno::ENOENT)? else {
            return Err(Errno::ENOENT);
        };
        let &child_ino = children.get(name).ok_or(Errno::ENOENT)?;
        let node = self.nodes.get(&child_ino).ok_or(Errno::ENOENT)?;
        let attr = Self::node_attr(child_ino, node, uid, gid);
        Ok((attr, Generation(0)))
    }

    pub(crate) fn do_getattr(&self, ino: u64, uid: u32, gid: u32) -> Result<FileAttr, Errno> {
        let node = self.nodes.get(&ino).ok_or(Errno::ENOENT)?;
        Ok(Self::node_attr(ino, node, uid, gid))
    }

    pub(crate) fn do_read(&self, ino: u64, offset: u64, size: u32) -> Result<Vec<u8>, Errno> {
        let Node::File { read } = self.nodes.get(&ino).ok_or(Errno::ENOENT)? else {
            return Err(Errno::ENOENT);
        };
        let file = read();
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

    pub(crate) fn do_readlink(&self, ino: u64) -> Result<Vec<u8>, Errno> {
        let Node::Symlink { target } = self.nodes.get(&ino).ok_or(Errno::ENOENT)? else {
            return Err(Errno::ENOENT);
        };
        Ok(target().into_bytes())
    }

    pub(crate) fn do_readdir(
        &self,
        ino: u64,
        offset: u64,
    ) -> Result<Vec<(u64, FileType, String)>, Errno> {
        let Node::Dir { children } = self.nodes.get(&ino).ok_or(Errno::ENOENT)? else {
            return Err(Errno::ENOENT);
        };

        let mut entries: Vec<(u64, FileType, String)> = Vec::new();
        entries.push((ino, FileType::Directory, ".".to_owned()));
        entries.push((1, FileType::Directory, "..".to_owned()));

        let mut sorted_children: Vec<_> = children.iter().collect();
        sorted_children.sort_by_key(|(name, _)| (*name).clone());
        for (name, child_ino) in &sorted_children {
            let child_ino = **child_ino;
            if let Some(node) = self.nodes.get(&child_ino) {
                entries.push((child_ino, Self::file_type(node), (*name).clone()));
            }
        }

        let skip = usize::try_from(offset).unwrap_or(usize::MAX);
        Ok(entries.into_iter().skip(skip).collect())
    }

    fn node_attr(ino: u64, node: &Node, uid: u32, gid: u32) -> FileAttr {
        match node {
            Node::Dir { .. } => FileAttr {
                ino: INodeNo(ino),
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
            Node::File { read } => {
                let file = read();
                let size = file.data.len() as u64;
                let mtime = file.mtime.unwrap_or(SystemTime::UNIX_EPOCH);
                #[allow(clippy::cast_possible_truncation)] // mode fits in u16 by construction
                let perm = file.mode.map_or(0o444, |m| m as u16);
                FileAttr {
                    ino: INodeNo(ino),
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
            Node::Symlink { target } => {
                let t = target();
                FileAttr {
                    ino: INodeNo(ino),
                    size: t.len() as u64,
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
                }
            }
        }
    }

    fn file_type(node: &Node) -> FileType {
        match node {
            Node::Dir { .. } => FileType::Directory,
            Node::File { .. } => FileType::RegularFile,
            Node::Symlink { .. } => FileType::Symlink,
        }
    }
}
