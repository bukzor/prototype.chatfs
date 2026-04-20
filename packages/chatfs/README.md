# chatfs

Lazy filesystem for chat conversations (claude.ai, ChatGPT).

Top-level Python package and CLI. Exposes the `chatfs` command; coordinates
capture, extraction, rendering, and the FUSE mount daemon.

Status: pre-alpha. The CLI is a stub.

## Layout

```
packages/chatfs/
├── pyproject.toml
├── README.md
└── lib/chatfs/
    ├── __init__.py
    ├── cli.py        # `chatfs` entry point
    └── layer/        # Legacy scaffolding (superseded, pending rework)
```

## Install

From the repo root:

```bash
uv sync
```

The workspace root declares `chatfs` as a default dependency, so `uv sync`
installs it and puts `chatfs` on `PATH`.

## Design

See `docs/dev/design.kb/` at the repo root for the layered design knowledge
(mission → goals → requirements → design). Decision rationale is inline with
each entry.
