"""
chatfs.layer.vfs - M2-VFS Layer (Normalized JSONL tools)

The VFS layer provides provider-normalized JSONL tools.

All VFS modules follow the JSONL contract:
- Read JSONL from stdin (one JSON object per line)
- Write JSONL to stdout (one JSON object per line)
- Log errors to stderr
- Exit 0 on success, non-zero on failure
- No interactive features (colors, progress bars, prompts)

Status: Not yet implemented. Will be created after M1-CLAUDE.
"""
