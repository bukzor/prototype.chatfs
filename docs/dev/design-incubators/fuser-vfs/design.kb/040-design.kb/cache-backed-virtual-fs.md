---
why:
  - ../030-requirements.kb/serve-static-directory-tree.md
  - ../030-requirements.kb/no-work-on-read.md
---

# Cache-Backed Virtual Filesystem

The VFS presents a virtual directory tree whose contents are backed by a real
directory on disk (the cache). The FUSE layer maps virtual paths to cache paths
and serves file contents directly from the cache.

```
Virtual (FUSE mount)              Cache (real filesystem)
/mnt/llmfs/chatgpt/              ~/.cache/llmfs/chatgpt/
├── conversations/                ├── conversations/
│   └── abc123/                   │   └── abc123/
│       └── branch-main.md  ───→  │       └── current/branch-main.md
└── status                        └── (generated dynamically)
```

The VFS never modifies the cache. Cache updates happen externally (via the sync
pipeline) and the VFS picks them up on next read.
