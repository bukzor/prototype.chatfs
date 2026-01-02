# Devlog: 2025-10-30

## Focus

Establish project documentation structure and design foundation before
implementation.

## What Happened

### Completed

- **Structured ideas into tiers** (tier 0: MVP, tier 1: probably, tier 2: maybe,
  tier 3: later)

  - Outcome: Clear priority separation, defer ChatGPT/Gemini/knowledge-store
    features

- **Identified subsystems** (lazy filesystem, fork management, write operations,
  knowledge management)

  - Outcome: Fork representation is architecturally critical, blocks write
    operations

- **Created documentation structure**

  - Core files: README.md, HACKING.md, CLAUDE.md, STATUS.md
  - Design docs: design-rationale.md, technical-design.md, development-plan.md
  - Devlog structure: docs/dev/devlog/ with README and dated entries
  - Outcome: Follows meta-documentation standard, LLM-friendly multi-session
    continuity

- **Isolated fork representation problem**
  - Created design-incubators/fork-representation/ subdirectory
  - Documented problem, candidate approaches, investigation plan
  - Wrote investigate-forks.py script for API exploration
  - Outcome: Complex problem separated from main implementation path

### Attempted

- **Considered starting implementation** (Milestone 1: Plumbing tools)
  - Outcome: User decided to document first, defer implementation

### Discovered

- **Plumbing/porcelain split enables multiple futures**

  - JSONL plumbing works with jq/Unix tools NOW
  - Easy capnshell migration later (swap serialization)
  - Feeds into TBD? (modular AI assistant) design

- **Fork representation is a foundation decision**

  - Affects: directory structure, data format, write operations, CLI design
  - Must resolve before implementing append/fork/amend
  - Can implement read-only functionality (M1) without solving this

- **Documentation-first valuable for multi-session LLM collaboration**
  - Explicit design rationale prevents repeating discussions
  - STATUS.md + devlog/ provide session continuity
  - Tiered detail (summary → deep dive) optimizes context loading

## Decisions Made

### Plumbing/Porcelain Split

**Decision:** Build as separate JSONL-based plumbing tools + future porcelain
wrappers

**Rationale:**

- Works with existing Unix tools (jq, grep) immediately
- Cheap capnshell migration (just serialization swap)
- Informs future tool design (learn what compositions matter)
- Aligns with "DIY/composable" philosophy

**Alternatives:** Monolithic CLI (faster to MVP, but less flexible)

**Impact:** All tool design, testing strategy, capnshell integration path

Documented in:
[../design-rationale.md#plumbing-porcelain-split]

### JSONL for Data Interchange

**Decision:** Use JSONL (JSON Lines) instead of plain JSON or capnproto

**Rationale:**

- Streaming-friendly (process line-by-line)
- Works with jq now
- Easy capnproto migration later
- Simple testing (echo + pipe)

**Alternatives:** Plain JSON (not streaming), capnproto (premature, needs
capnshell)

**Impact:** Plumbing I/O format, testing approach, future migration path

Documented in:
[../design-rationale.md#jsonl-for-data-interchange]

### Documentation Before Implementation

**Decision:** Build comprehensive documentation structure before writing code

**Rationale:**

- Multi-session project (weeks/months)
- LLM collaboration needs explicit context
- Cheaper to change docs than refactor code
- Design exploration (forks, porcelain, capnshell) needs thought

**Alternatives:** Code first, document later (faster to prototype, harder to
maintain direction)

**Impact:** Project timeline (slower to code), session continuity, design
quality

Documented in:
[../design-rationale.md#documentation-first-approach]

### Lazy Filesystem Model

**Decision:** Create files/directories on-demand, track staleness via mtime

**Rationale:**

- Scales (works for 10 or 10,000 conversations)
- Fast (only fetch when accessed)
- Offline-friendly (files persist)
- No FUSE dependency

**Alternatives:** Eager sync (slow, wasteful), FUSE (complex, requires root)

**Impact:** Cache implementation, user experience, performance

Documented in:
[../design-rationale.md#lazy-filesystem-model]

## Open Questions

1. **Should we start M1 (plumbing implementation) now or resolve fork
   representation first?**

   - Context: Read-only plumbing doesn't need forks, but forks are
     architecturally critical
   - Leaning: Start M1, resolve forks in parallel or defer to M3

2. **Which fork representation approach is best?**

   - Context: Flat naming, nested directories, git-like refs, or virtual paths?
   - Needs: Real API investigation of how claude.ai represents forks
   - See: design-incubators/fork-representation/

3. **Should we prioritize multi-provider (M2) or porcelain UX next?**
   - Context: After M1 complete, what's more valuable?
   - Depends: User needs (Claude-only vs multi-provider)

## Next Session

**Start here:**

- Finish documentation structure:
  - Move fork-representation-design/ → design-incubators/fork-representation/
  - Create docs/dev/technical-design/provider-interface.md
  - Update STATUS.md with completed documentation tasks

**Then decide:**

- Option A: Start M1 implementation (plumbing tools)
- Option B: Investigate fork representation (run investigate-forks.py with real
  data)
- Option C: Continue design exploration (porcelain UX, capnshell integration)

**Blockers:** None (ready to implement or explore)

## Links

- [../../../STATUS.md] - Updated with M0 progress
- [../design-rationale.md] - Core design decisions
- [../development-plan.md] - Milestone roadmap
- [../../../design-incubators/fork-representation/] -
  Fork design exploration

## Related Projects Context

This session explored connections to:

- **capnshell:** Shell using capnproto for structured data (nushell competitor)
- **aider-ng:** Modular AI coding assistant (aider/claude-code competitor)

chatfs serves as a test case for composable tool design. Plumbing tools will
work in capnshell by swapping JSONL → capnproto serialization. The aider-ng
assistant could use chatfs to pull relevant past conversations as context.

These are separate projects but share philosophy: small, composable,
DIY-friendly tools.
