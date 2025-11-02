"""
chatfs.plumbing - Low-level JSONL-based tools

All plumbing modules follow the contract:
- Read JSONL from stdin (one JSON object per line)
- Write JSONL to stdout (one JSON object per line)
- Log errors to stderr
- Exit 0 on success, non-zero on failure
- No interactive features (colors, progress bars, prompts)
"""
