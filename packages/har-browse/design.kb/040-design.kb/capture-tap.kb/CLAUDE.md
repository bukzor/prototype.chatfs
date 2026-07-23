# Capture Tap — Design Sub-Decisions

Three coupled decisions that together define how capture attaches to
the browser and what it emits: where we tap the byte stream, what the
emitted record looks like, and how in-page code stamps checkpoints
into it.

## What belongs here

- One file per sub-decision of the capture architecture, each stating
  the chosen approach and the alternatives it beat
- Cross-cutting to all of BB1; not any one component's internals

## What does NOT belong

- Which library implements the decision today (→ `050-components.kb/`)
- The cut/drain completeness model (→ `../capture-cut-model.md`, a
  sibling design entry, not part of this sub-decision set)
