# How to chatfs

Pull a chat conversation out of a provider's web UI and onto your disk as
markdown.

Supported providers: **claude.ai**, **chatgpt.com**, **AI Studio**.

## What works today

The pipeline runs as a hand-driven CLI: you give it a conversation URL, a
browser opens, you click a button, and markdown lands on disk.

Not yet: the FUSE mount (`/mnt/llmfs/...`) and the `chatfs` command itself.
Those are designed but unbuilt — the README describes the destination, this
document describes the road.

## Setup

Once per checkout, from the repo root:

```bash
uv sync        # Python deps, into .venv/
pnpm install   # Node deps; puts `har-browse` on your PATH
```

The commands below are `python -m ...`, run from the incubator directory, so
that `.venv` needs to be active (direnv does this for you in this checkout).

Node 22+ is required. You do **not** need an API key — capture drives your
own browser session, so whatever you can read while logged in, you can pull.

## Pull one conversation

```bash
cd docs/dev/design-incubators/chatfs-cli-mockup
python -m chatfs.provider.claude.conversation.url_browse https://claude.ai/chat/$UUID
```

Swap `claude` for `chatgpt` or `aistudio`; the module path is the only thing
that changes.

A browser window opens on the conversation. Log in if you need to, let the
page finish loading, then click **Done Capturing** in the overlay. The command
runs the rest of the pipeline and exits.

Your login persists in a dedicated browser profile under
`~/.cache/har-browse/profile/`, so you only log in once — this browser is
separate from your daily one.

## Where it lands

Everything goes under `chatfs.demo/<provider>/`:

```
.chat/$UUID/
    chat.md         # the whole conversation, one file
    messages/       # one .md + .json per turn
    (.data/ holds the raw capture — see "When it goes wrong")
Created=YYYY/MM/DD/$TIMESTAMP/$TITLE -> ../../../../.chat/$UUID/
```

Two ways in, same bytes: `.chat/$UUID/` if you know the UUID, or browse the
date tree by title. The date-tree entry is a symlink to the chat dir, so
`cat Created=2026/07/26/*/My\ Chat/chat.md` just works.

`chat.md` renders the live conversation path as a sequence of turns. Edited
and regenerated messages appear as nested blockquoted asides at the point
where the conversation forked, so nothing you said is silently dropped.

## Other things you can do

Re-render from bytes already captured (no browser, no network):

```bash
python -m chatfs.provider.claude.conversation.url_render https://claude.ai/chat/$UUID
```

Pull many conversations — capture the sidebar index first, which lays down a
chat dir per conversation, then walk them:

```bash
python -m chatfs.provider.claude.index.browse | python -m chatfs.provider.claude.index.splat
python -m chatfs.provider.claude.conversation.path_browse chatfs.demo/claude/.chat/$UUID/
python -m chatfs.provider.claude.conversation.path_render chatfs.demo/claude/.chat/$UUID/
```

Throw one away — moves the chat dir and its symlinks to the repo's `trash/`:

```bash
python -m chatfs.provider.claude.conversation.url_trash https://claude.ai/chat/$UUID
```

## When it goes wrong

Every stage rebuilds its output from scratch, so **re-running is always safe**
and is the first thing to try.

The raw capture stays on disk at `.chat/$UUID/.data/` — `cdp.jsonl` (the
browser's network traffic) and `conversation.json` (the provider's own
conversation document, plucked out of it). A failure leaves those in place to
look at, and the previous successful capture is never destroyed by a failed
one.

**"no sidebar index page included $UUID"** — capturing by URL relies on the
page also loading your conversation list, which is where the title and
timestamp come from. If it didn't, run the bulk path above instead:
`index.browse | index.splat`, then `path_browse`.

**Capture succeeded but the conversation isn't in it** — providers hydrate
from their own client-side cache and may never hit the network on a revisit.
Local storage is cleared before navigating to prevent exactly this; if you
opted out with `har-browse --keep-origin-storage`, don't.

## Deeper

- Stage-by-stage walkthrough, and why the layout is shaped this way:
  [dev/design-incubators/chatfs-cli-mockup/README.md]
- Where all this is headed: [../README.md]
- The design knowledge behind it: [dev/design.kb/]
