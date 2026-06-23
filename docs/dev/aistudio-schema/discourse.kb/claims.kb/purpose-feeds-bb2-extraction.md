---
status: contested
likelihood: 0.4
depends:
  - claims.kb/schema-recoverable-from-bundle.md
  - claims.kb/getter-recovery-is-partial.md
tags: [chatfs, bb2, inference, doubt]
---

The recovered schema exists to let chatfs's extraction stage (BB2) parse AI
Studio's JSPB/protobuf conversation payloads into the project's JSONL.

**This is the assistant's inference, NOT stated in the README.** The README
justifies *how* and *why it works*, but never names a downstream consumer.
Supporting circumstantial evidence: the toolkit sits under `docs/dev/`, and a
sibling claim file (`aistudio-jspb-prompt-shape.md`) is cited for cross-checking
field numbers — consistent with feeding extraction.

**Counter-evidence found (likelihood lowered 0.55 → 0.4).** The working AI
Studio extractor already exists: `chatfs_aistudio_conversation_pluck.jq`. It
reads the conversation out of the `ResolveDriveResource` payload by **hard-coded
JSPB positions**, and does *not* import this toolkit's recovered field numbers.
And this toolkit's getter method does not even recover the turn/content fields
the extractor needs (`claims.kb/getter-recovery-is-partial.md`). So the toolkit
is not the runtime feed for BB2.

That reweights the alternatives toward **schema-as-documentation / validation**:
the toolkit names and cross-checks the very positions the `.jq` hard-codes
(against `aistudio-jspb-prompt-shape.md`), making it a maintenance/disambiguation
aid for the positional extractor rather than a code dependency. Still the
assistant's inference; resolve by asking the user.

Competing possibilities not ruled out: a one-off exploratory probe; input to
design/decision-making rather than to running code; or schema documentation as
an end in itself. Hence `contested`, likelihood ~0.55. Resolve by asking the
user or finding a BB2 consumer that imports these field numbers.
