# design-incubators/ - Active Design Problems

Isolated workspaces for exploring unsolved design problems before committing to
an approach.

## What Belongs Here

**Self-contained design explorations** for problems that:

- Affect multiple components or have broad architectural impact
- Have multiple viable approaches requiring investigation
- Need prototyping or experimentation across multiple sessions
- Block implementation but aren't urgent to resolve

Each subdirectory should:

- Have a clear problem statement (CLAUDE.md)
- Document investigation process (README.md)
- Include exploration scripts, prototypes, or experiments
- Conclude with a decision (DECISION.md when resolved)

## Lifecycle

1. **Create:** When hitting an architectural decision that needs exploration
2. **Explore:** Run experiments, document findings, prototype alternatives
3. **Decide:** Write DECISION.md with chosen approach and rationale
4. **Integrate:** Move lessons into docs/dev/, update technical-design.md
5. **Archive or Delete:** Remove incubator when no longer referenced

## Guidelines

Use an incubator when you find yourself saying:

- "There are 3 ways to do this, and each has trade-offs..."
- "I need to prototype this to understand the implications"
- "This decision affects too many things to rush it"
