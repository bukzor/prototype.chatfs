# chatfs

Lazy filesystem for chat conversations (claude.ai, ChatGPT).

Top-level Python package and CLI. Exposes the `chatfs` command; coordinates
capture, extraction, rendering, and the FUSE mount daemon.

Status: pre-alpha. The CLI is a stub — it parses `--version` and exits.

The pipeline that actually captures and renders conversations today is the
hand-driven CLI at `docs/dev/design-incubators/chatfs-cli-mockup/`; see
`docs/how-to-chatfs.md` to run it. This package is where that graduates to
(`.claude/todo.kb/2026-07-13-000-graduation-and-integration.md`).

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
