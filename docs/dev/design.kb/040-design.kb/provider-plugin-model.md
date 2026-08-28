---
why:
  - ../030-requirements.kb/provider-agnostic-interface.md
source:
  - conversations.cleaned/06-design-spec-project-handoff/167.assistant.text.md#2
---

# Provider Plugin Model

chatfs is provider-agnostic. Each chat service (Claude, ChatGPT, Gemini, etc.)
is a provider module implementing a common interface over the black boxes plus
cache layout rules.

**A provider defines:**

1. How to parse a `ConversationRef` (URL, ID, "active tab")
2. Where artifacts and outputs live in the cache
3. How to invoke BB1 (capture), BB2 (extract), BB3 (emit)
4. How to detect staleness (manual-only, TTL, version file)
5. What the mounted directory structure looks like

The filesystem core never needs to know message schemas — only that the
provider can materialize a conversation into cache when asked.

What building three providers showed about where the provider/universal
boundary actually falls is recorded at
`packages/chatfs-cli/design.kb/040-design.kb/provider-plugin-model.md`:
provider-shaped logic collapsed to two tiny adapters (a 3-value tuple
plus timestamp parser for placement, a 2-value tuple for capture), with
extractors and splat genuinely provider-only.

> [!QUESTION] one multi-provider mount root, or one mount per cache dir?
> The original sketch mounts providers side by side under
> `/mnt/llmfs/<provider>/` (`chatgpt/`, `claude.ai/`, ...). The cache
> tree now has that shape: `--cache` names a cache holding every
> provider, each writing under `$cache/<provider>/`
> (`docs/dev/technical-policy.kb/path-ownership.md`, 2026-08-28). One
> mount over one cache therefore already serves every provider, which
> collapses most of the original either/or. Still settles with the
> mount MVP (graduation child 003); what remains genuinely open is
> narrower — whether the daemon ever composes *several* caches into a
> single tree, or whether that stays the consumer's arrangement of
> mounts.

> [!QUESTION] is a declarative provider manifest still wanted?
> The sketched per-provider configuration record — accepted `conv_ref`
> forms, artifact landing paths, cache locations, TTL/invalidation
> rules, how to report "needs user interaction" — was never built.
> Three providers landed as code-level adapters (see the package
> lessons entry above) with no manifest. Settles when the daemon needs
> to enumerate or configure providers it does not link against; until
> then the adapter shape may simply have superseded this.
