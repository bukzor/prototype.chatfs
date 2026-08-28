# 2026-08-28 Provider becomes a path segment, and the CLI stops asking which one

## Focus

Started as a bug report: `chatfs-claude-conversation-path-browse` pointed at
a *chatgpt* chat dir, dying on `assert is_index_item(meta), meta` and dumping
twenty fields of JSON. The diagnosis was one line — wrong driver — but the
question it opened was why the tool let it happen, and that ran all day.

## What happened

1. **The cache root holds every provider** (`befa423`). `--cache` was the
   provider root itself, so `~/chats/{claude,chatgpt,aistudio}/` was a naming
   convention the user maintained by hand, one `--cache` value per provider.
   `extract_cache` now takes the provider and returns `$cache/$provider/`.

   The user corrected me here, and the correction was the pivot of the whole
   session. I had described the code's behavior accurately and then treated it
   as the design; their reading — `--cache` is `~/chats`, provider is the next
   segment — was both what they intended and strictly better, because it makes
   the provider *readable from any path* downstream.

   Evidence it had already bitten: `~/chats/.data/` held 80MB of spill from
   two runs that passed the container as `--cache` (a claude index browse, and
   a chatgpt capture whose `conversation.json` came out empty). Moved to
   `trash/chats-root-spill.20260828T132232/`. No data migration was needed —
   `~/chats/<provider>/` is already exactly the layout the change produces.

2. **The `provider` segment gets written in command names** (`c930684`).
   `cli-command-shape.md` claimed a command's kebab name equals its module
   path; `pyproject.toml` said it again in a comment. Neither was true — the
   module path carried `chatfs.provider.claude.…` while the command silently
   elided `provider`. Writing it makes the stated rule true and frees the bare
   `chatfs-<noun>-<verb>` names. Name-only: no runtime coupling existed,
   since every occurrence under `lib/` is a docstring and stages invoke each
   other by module path.

3. **Dispatching forms** (`904cda0`, `bf9513f`, `3c15681`).
   `chatfs-conversation-{url,path}-{browse,render}` and
   `chatfs-conversation-render` read the provider off the locator the user
   already typed. `HOST` joined `PROVIDER` in each `layout`, and `url_for` is
   now written in terms of it, so the dispatch map cannot drift from the URLs
   this codebase emits.

4. **The module↔command mapping is enforced, not trusted** (`926b5d8`).
   Derived from `ast`, compared against `[project.scripts]`: bijective at
   34/34 when pinned. It caught its first omission the same hour, when
   `conversation/render.py` was written without its entry.

## Decisions

### The provider is read, never sniffed

**Rationale:** The obvious way to dispatch a path is to sniff `meta.json`'s
shape. It is unsound here and would have looked fine indefinitely: chatgpt's
and aistudio's `is_index_item` differ only in which *second* timestamp field
they carry and its JSON type, and `aistudio/types.py` says out loud that its
synthesized shape "echoes the chatgpt one". Worse, the chatgpt half is an
upstream payload `path-ownership.md` requires we keep verbatim — so the
disjointness is a property we neither designed nor control.

**Alternatives considered:** (a) shape sniffing — rejected above; (b) a
`provider` key in `meta.json` — forbidden by the 2026-08-27 verbatim ruling;
(c) a `.data/$UUID/provider` sibling file — sound, but obviated once the
provider became a path segment, which is free and self-describing under `ls`.

### Only an address-shaped argument earns a dispatching form

**Rationale:** `conversation render` takes a chat-dir address and dispatches.
`conversation splat` takes a `conversation.json` and an output dir — a file
and a destination, and `path_render` passes a *staged scratch sibling* for
the second, which need not sit in a cache at all. A provider inferred from
those would be right by coincidence, the same failure mode as (a) above.
Recorded as vocabulary in `cli-command-shape.md` so splat's missing twin
reads as a decision rather than an oversight.

### The dispatcher parses only enough to name the provider

**Rationale:** It forwards argv untouched to `python -m
chatfs.provider.<p>.conversation.<leaf>`. The moment it parsed `--cache`, or
imported a stage, it would become a second copy of a leaf's contract, free to
drift from it. Owning only the routing decision is what prevents that.

### Entry points stay static in `pyproject.toml`

**Rationale:** Asked whether the now-reliable mapping could drive entry points
"as code". It can — hatchling supports `dynamic = ["scripts"]` with a
`hatch_build.py` metadata hook. Rejected for now: `pyproject.toml` would stop
stating the CLI surface, so a reader would have to run the build to learn what
installs. A test gets the same protection and keeps the manifest readable.

## Conventions Established

- A cache is a container of provider roots; only the cache is nameable on the
  command line. Passing a provider root to `--cache` nests a second one inside
  it, which is now the documented failure mode rather than a silent spill.
- Provider-shaped constants (`PROVIDER`, `HOST`) live in that provider's
  `layout`, and anything derived from them (`url_for`, the dispatch map) is
  written in terms of them rather than repeating the literal.
- Historical hits are left stale during a rename — devlog bodies and completed
  `todo.kb/` children describe what was true on their date. Same precedent as
  the incubator rename.

## Open Questions

- `provider-plugin-model.md`'s mount question had a premise this session
  falsified ("the cache contract has no `<provider>/` level inside it"). The
  premise is corrected and the question narrowed — one mount over one cache
  now serves every provider — but the residual (does the daemon ever compose
  *several* caches into one tree?) still settles with graduation child 003.
- Whether to generate `[project.scripts]` from `entry_points_test.py`'s
  `modules_defining_main()`. Filed in `todo.md`; the test already is the
  generator.

## References

- `docs/dev/technical-policy.kb/path-ownership.md` — cache root vs provider root
- `packages/chatfs-cli/design.kb/040-design.kb/cli-command-shape.md` — dispatching form
- `packages/chatfs-cli/design.kb/040-design.kb/driver-model.md` — dispatch as a third surface
- Commits: `befa423`, `c930684`, `904cda0`, `bf9513f`, `926b5d8`, `3c15681`
