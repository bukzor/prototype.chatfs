# docs/dev/design/ - Component Design Details

Detailed specifications for individual components and subsystems.

## What Belongs Here

**Component-level design documents** that would make technical-design.md too
long:

- API client implementation details
- Cache layer algorithms and data structures
- Data format specifications (JSONL schemas, message formats)
- Specific subsystem architectures

Each document should:

- Focus on a single component or subsystem
- Include implementation details (data structures, algorithms, edge cases)
- Be referenced from technical-design.md with a brief summary

## What Doesn't Belong Here

- High-level architecture (stays in technical-design.md)
- Why decisions were made (goes in docs/dev/rationale/)
- Implementation plans (goes in docs/dev/plan/)

## Guidelines

Create a file here when:

- Component documentation exceeds ~100 lines
- Details are needed but would clutter technical-design.md
- Multiple developers will reference it independently

Link from technical-design.md with a 1-2 sentence summary.
