use std::ffi::OsStr;
use std::time::Duration;

use fuser::{
    Errno, FileHandle, Filesystem, INodeNo, LockOwner, OpenFlags, ReplyAttr, ReplyData,
    ReplyDirectory, ReplyEntry, Request,
};

use crate::node_ops::NodeOps;

const TTL: Duration = Duration::from_secs(0); // no caching — always call back

/// Thin adapter — delegates to pure `NodeOps` methods.
pub(crate) struct FuseFs {
    ops: NodeOps,
}

impl FuseFs {
    pub(crate) fn new(ops: NodeOps) -> Self {
        Self { ops }
    }
}

impl Filesystem for FuseFs {
    fn lookup(&self, req: &Request, parent: INodeNo, name: &OsStr, reply: ReplyEntry) {
        let Some(name_str) = name.to_str() else {
            reply.error(Errno::ENOENT);
            return;
        };
        match self.ops.do_lookup(parent, name_str, req.uid(), req.gid()) {
            Ok((attr, generation)) => reply.entry(&TTL, &attr, generation),
            Err(e) => reply.error(e),
        }
    }

    fn getattr(&self, req: &Request, ino: INodeNo, _fh: Option<FileHandle>, reply: ReplyAttr) {
        match self.ops.do_getattr(ino, req.uid(), req.gid()) {
            Ok(attr) => reply.attr(&TTL, &attr),
            Err(e) => reply.error(e),
        }
    }

    fn readlink(&self, _req: &Request, ino: INodeNo, reply: ReplyData) {
        match self.ops.do_readlink(ino) {
            Ok(data) => reply.data(&data),
            Err(e) => reply.error(e),
        }
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
        match self.ops.do_read(ino, offset, size) {
            Ok(data) => reply.data(&data),
            Err(e) => reply.error(e),
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
        match self.ops.do_readdir(ino, offset) {
            Ok(entries) => {
                for (i, (ino, kind, name)) in entries.into_iter().enumerate() {
                    let offset_next = offset + i as u64 + 1;
                    if reply.add(ino, offset_next, kind, &name) {
                        break;
                    }
                }
                reply.ok();
            }
            Err(e) => reply.error(e),
        }
    }
}
