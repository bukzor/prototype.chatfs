use std::collections::HashMap;
use std::ffi::OsStr;
use std::time::{Duration, SystemTime};

use fuser::{
    Errno, FileAttr, FileHandle, FileType, Filesystem, Generation, INodeNo, LockOwner, OpenFlags,
    ReplyAttr, ReplyData, ReplyDirectory, ReplyEntry, Request,
};

use crate::node::Node;

const TTL: Duration = Duration::from_secs(0); // no caching — always call back

pub(crate) struct FuseFs {
    nodes: HashMap<u64, Node>,
}

impl FuseFs {
    pub(crate) fn new(nodes: HashMap<u64, Node>) -> Self {
        Self { nodes }
    }

    fn dir_attr(&self, ino: u64, req: &Request) -> FileAttr {
        FileAttr {
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
            uid: req.uid(),
            gid: req.gid(),
            rdev: 0,
            blksize: 512,
            flags: 0,
        }
    }

    fn file_attr(&self, ino: u64, node: &Node, req: &Request) -> FileAttr {
        let file = match node {
            Node::File { read } => read(),
            Node::Dir { .. } => return self.dir_attr(ino, req),
        };
        let size = file.data.len() as u64;
        let mtime = file.mtime.unwrap_or(SystemTime::UNIX_EPOCH);
        let perm = file.mode.map_or(0o444, |m| m as u16);
        FileAttr {
            ino: INodeNo(ino),
            size,
            blocks: (size + 511) / 512,
            atime: mtime,
            mtime,
            ctime: mtime,
            crtime: mtime,
            kind: FileType::RegularFile,
            perm,
            nlink: 1,
            uid: req.uid(),
            gid: req.gid(),
            rdev: 0,
            blksize: 512,
            flags: 0,
        }
    }
}

impl Filesystem for FuseFs {
    fn lookup(&self, req: &Request, parent: INodeNo, name: &OsStr, reply: ReplyEntry) {
        let parent_ino = u64::from(parent);
        let Some(Node::Dir { children }) = self.nodes.get(&parent_ino) else {
            reply.error(Errno::ENOENT);
            return;
        };
        let Some(name_str) = name.to_str() else {
            reply.error(Errno::ENOENT);
            return;
        };
        let Some(&child_ino) = children.get(name_str) else {
            reply.error(Errno::ENOENT);
            return;
        };
        let Some(node) = self.nodes.get(&child_ino) else {
            reply.error(Errno::ENOENT);
            return;
        };
        let attr = self.file_attr(child_ino, node, req);
        reply.entry(&TTL, &attr, Generation(0));
    }

    fn getattr(&self, req: &Request, ino: INodeNo, _fh: Option<FileHandle>, reply: ReplyAttr) {
        let ino_val = u64::from(ino);
        let Some(node) = self.nodes.get(&ino_val) else {
            reply.error(Errno::ENOENT);
            return;
        };
        let attr = match node {
            Node::Dir { .. } => self.dir_attr(ino_val, req),
            Node::File { .. } => self.file_attr(ino_val, node, req),
        };
        reply.attr(&TTL, &attr);
    }

    fn read(
        &self,
        _req: &Request,
        ino: INodeNo,
        _fh: FileHandle,
        offset: u64,
        size: u32,
        _flags: OpenFlags,
        _lock_owner: Option<LockOwner>,
        reply: ReplyData,
    ) {
        let ino_val = u64::from(ino);
        let Some(Node::File { read }) = self.nodes.get(&ino_val) else {
            reply.error(Errno::ENOENT);
            return;
        };
        let file = read();
        let data = file.data.as_bytes();
        let offset = offset as usize;
        if offset >= data.len() {
            reply.data(&[]);
        } else {
            let end = (offset + size as usize).min(data.len());
            reply.data(&data[offset..end]);
        }
    }

    fn readdir(
        &self,
        _req: &Request,
        ino: INodeNo,
        _fh: FileHandle,
        offset: u64,
        mut reply: ReplyDirectory,
    ) {
        let ino_val = u64::from(ino);
        let Some(Node::Dir { children }) = self.nodes.get(&ino_val) else {
            reply.error(Errno::ENOENT);
            return;
        };

        // Build entry list: `.`, `..`, then children sorted by name
        let mut entries: Vec<(u64, FileType, String)> = Vec::new();
        entries.push((ino_val, FileType::Directory, ".".to_owned()));
        entries.push((1, FileType::Directory, "..".to_owned()));

        let mut sorted_children: Vec<_> = children.iter().collect();
        sorted_children.sort_by_key(|(name, _)| (*name).clone());
        for (name, child_ino) in &sorted_children {
            let child_ino = **child_ino;
            let kind = match self.nodes.get(&child_ino) {
                Some(Node::Dir { .. }) => FileType::Directory,
                Some(Node::File { .. }) => FileType::RegularFile,
                None => continue,
            };
            entries.push((child_ino, kind, (*name).clone()));
        }

        for (i, (ino, kind, name)) in entries.into_iter().enumerate().skip(offset as usize) {
            let offset_next = (i + 1) as u64;
            if reply.add(INodeNo(ino), offset_next, kind, &name) {
                // Buffer full
                break;
            }
        }
        reply.ok();
    }
}
