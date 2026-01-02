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

**Multi-phase incubators:** Some design problems span multiple milestones. For example, fork-representation splits into 3 phases (M1-CLAUDE API investigation, M2-VFS normalization, M3-CACHE filesystem layout). Each phase informs the next.

## Active Incubators

### fork-representation/

**Blocks:** M1-CLAUDE (Phase 1), M2-VFS (Phase 2), M3-CACHE (Phase 3)

**Multi-phase incubator** - splits across 3 milestones:

**Phase 1 (M1-CLAUDE):** What does Claude API return for forked conversations?
**Phase 2 (M2-VFS):** What should normalized API provide for forks across providers?
**Phase 3 (M3-CACHE):** How do we represent forks on disk?

**Status:** Phase 1 (API investigation) needed for M1-CLAUDE

### chat-provider-normalization/

**Blocks:** M2-VFS implementation

**Questions:**
1. How to normalize across chat LLM providers (Claude, ChatGPT, Google AI Studio)?
2. Pure abstraction vs. abstraction+extensions approach?
3. How to handle provider-specific features (forks, streaming)?

**Status:** Depends on M1-CLAUDE findings, needs research on ChatGPT/Google AI Studio

### multi-domain-support/

**Blocks:** Long-term architecture strategy

**Questions:**
1. Should chatfs support only chat providers or expand to Linear/GitHub/AWS/GCP?
2. If expanding: chat-only, universal abstraction, or tiered abstraction?
3. How much code can be shared across domains?

**Status:** Strategic decision, depends on M1-CLAUDE + chat provider normalization experience
