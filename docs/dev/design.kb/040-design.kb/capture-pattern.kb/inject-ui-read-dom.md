# Inject UI, Export from DOM

Same injected-button UX as `inject-ui-read-state.md`, but the button walks
the rendered DOM and builds a best-effort transcript rather than reading app
state.

**Pros.** More stable across internal-state refactors — the DOM is closer to
a public contract than the framework store.

**Cons.** Loses fork metadata and other structure that isn't rendered into
visible DOM. Producing a canonical graph from flat DOM is a lossy reverse.
