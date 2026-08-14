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
uv sync        # installs chatfs-cli and its commands into .venv/
pnpm install   # Node deps; puts `har-browse` on your PATH
```

That puts one command per pipeline stage on your PATH, named
`chatfs-<provider>-<noun>-<verb>` (activate `.venv` — direnv does this for
you in this checkout). They run from any directory; every command that isn't
addressed by an on-disk path takes `--cache <dir>`, the per-provider root it
reads and writes, in any position on the command line. There is deliberately
no default — pick a directory and keep using it, or export it once:

```bash
export CHATFS_CACHE=~/chats/claude
```

and drop `--cache` from every command below; an explicit `--cache` still
wins if you pass both.

Node 22+ is required. You do **not** need an API key — capture drives your
own browser session, so whatever you can read while logged in, you can pull.

## Pull one conversation

```bash
chatfs-claude-conversation-url-browse --cache ~/chats/claude https://claude.ai/chat/$UUID
```

Swap `claude` for `chatgpt` or `aistudio`; the command name is the only
thing that changes.

A browser window opens on the conversation. Log in if you need to, let the
page finish loading, then click **Done Capturing** in the overlay. The command
runs the rest of the pipeline and exits, printing the absolute path of the
resulting `chat.md` on stdout.

Your login persists in a dedicated browser profile under
`~/.cache/har-browse/profile/`, so you only log in once — this browser is
separate from your daily one.

Progress messages (what's being captured/splatted/rendered, and the
subprocess calls between stages) go to stderr and are silent by default; set
`DEBUG=1` to see them.

## Where it lands

Everything goes under the `--cache` directory:

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

`.chat/$UUID/.data` is an absolute symlink, so `cp -ar .chat/$UUID/
anywhere/` carries a chat dir out of the cache without leaving `.data`
dangling — it still resolves back into this cache's `.data/$UUID/`.

`chat.md` renders the live conversation path as a sequence of turns. Edited
and regenerated messages appear as nested blockquoted asides at the point
where the conversation forked, so nothing you said is silently dropped.

## Other things you can do

Re-render from bytes already captured (no browser, no network):

```bash
chatfs-claude-conversation-url-render --cache ~/chats/claude https://claude.ai/chat/$UUID
```

Pull many conversations — capture the sidebar index first, which lays down a
chat dir per conversation, then walk them (path-addressed commands need no
`--cache`; the path says which cache they're in):

```bash
chatfs-claude-index-browse --cache ~/chats/claude | chatfs-claude-index-splat --cache ~/chats/claude
chatfs-claude-conversation-path-browse ~/chats/claude/.chat/$UUID/
chatfs-claude-conversation-path-render ~/chats/claude/.chat/$UUID/
```

Throw one away — moves the chat dir and its symlinks to the cache root's own
`trash/`:

```bash
chatfs-claude-conversation-url-trash --cache ~/chats/claude https://claude.ai/chat/$UUID
```

The repo carries captured fixtures at
`docs/dev/design-incubators/chatfs-cli-mockup/chatfs.demo/<provider>` — point
`--cache` there to try the render stages without capturing anything.

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
`index-browse | index-splat`, then `path-browse`.

**Capture succeeded but the conversation isn't in it** — providers hydrate
from their own client-side cache and may never hit the network on a revisit.
Local storage is cleared before navigating to prevent exactly this; if you
opted out with `har-browse --keep-origin-storage`, don't.

## Deeper

- Stage-by-stage walkthrough, and why the layout is shaped this way:
  [packages/chatfs-cli/README.md](../packages/chatfs-cli/README.md)
- Where all this is headed: [../README.md]
- The design knowledge behind it: [dev/design.kb/]
