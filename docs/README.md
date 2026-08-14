# docs/ - Documentation

This directory contains all project documentation beyond the root-level quick
references.

## Documentation Map

**Start here based on your goal:**

- **New user? Want overview?** → [../README.md] - What the project does
- **Want to actually use it?** → [how-to-chatfs.md] - Pull a conversation down as markdown
- **Want to contribute?** → [../HACKING.md] - Setup and development workflow
- **Resume development session?** → Latest `../.claude/todo*`
- **Learn system architecture?** → [dev/design.kb/] - Layered design knowledge; decision rationale lives inline with each entry
- **Working with LLM assistant?** → [../CLAUDE.md] - Quick reference guide

**Recommended reading flow for new contributors:**

1. [../HACKING.md] - Setup and conventions
2. [dev/design.kb/] - Layered design (mission → goals → requirements → design), with rationale inline

## Structure

- **how-to-chatfs.md** - User-facing: how to pull conversations down today
- **dev/** - Developer-focused documentation (design, plans, logs)
- (future) **examples/** - Usage examples and tutorials for end users
- top-level namespace reserved for user-facing documentation.

## What Belongs Here

**Detailed documentation** that would clutter the root directory:

- Design rationale and decisions
- Technical specifications
- Development plans and milestones
- Session logs and history
- Usage examples and tutorials

[../README.md]: ../README.md
[how-to-chatfs.md]: how-to-chatfs.md
[../HACKING.md]: ../HACKING.md
[dev/design.kb/]: dev/design.kb/
[../CLAUDE.md]: ../CLAUDE.md
