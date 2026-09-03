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
`chatfs-provider-<provider>-<noun>-<verb>` (activate `.venv` — direnv
does this for you in this checkout), plus a shorter
`chatfs-<noun>-<locator>-<verb>` for each stage that can work out the
provider from the URL or path you hand it. They run from any directory.

Most take `--cache <dir>` — the cache they read and write — in any
position on the command line. Each provider gets its own `<provider>/`
subdirectory under it, appended for you, so one cache serves all three.
There's no default; pick a directory and keep using it, or export it
once:

```bash
export CHATFS_CACHE=~/chats
```

An explicit `--cache` overrides it.

Node 22+ is required. You do **not** need an API key — capture drives your
own browser session, so whatever you can read while logged in, you can pull.

## Pull one conversation

```bash
chatfs-conversation-url-browse --cache ~/chats https://claude.ai/chat/$UUID
```

The provider comes from the URL's host, so that same command takes a
`chatgpt.com` or `aistudio.google.com` link. Every dispatching command has a
`chatfs-provider-<provider>-…` twin naming one provider outright — the
dispatcher just picks which twin to run.

A browser window opens on the conversation. Log in if you need to, let the
page finish loading, then click **Done Capturing** in the overlay. The command
runs the rest of the pipeline and exits, printing the absolute path of the
resulting `chat.md` on stdout.

Your login persists in a dedicated browser profile under
`~/.cache/har-browse/profile/`, so you only log in once — this browser is
separate from your daily one.

Progress messages go to stderr and are silent by default; set `DEBUG=1` to
see them.

## Where it lands

Everything goes under the cache's provider subdirectory --
`~/chats/claude/` for the commands above:

```
.chat/$UUID/
    chat.md         # the whole conversation, one file
    messages/       # one .md + .json per turn
    (.data/ holds the raw capture — see "When it goes wrong")
Created=YYYY/MM/DD/$TIMESTAMP/$TITLE -> ../../../../.chat/$UUID/
```

Two ways in, same bytes: `.chat/$UUID/` if you know the UUID, or browse the
date tree by title.

`.chat/$UUID/.data` is an absolute symlink, so `cp -ar .chat/$UUID/
anywhere/` carries a chat dir out of the cache without leaving `.data`
dangling.

`chat.md` is the whole conversation as it currently reads, turn by turn.
Edited and regenerated messages appear as nested blockquoted asides at the
point where the conversation forked, so nothing you said is silently
dropped.

Forks read as asides only if the provider sent them. chatgpt's current
endpoints serve a conversation as one linear thread, so the text behind its
`<` `>` arrows is not in the capture. It still tells us *where* you edited a
turn, and that much survives into `chat.md`:

```
*prior revisions: not captured*
```

So `grep 'prior revisions:'` finds every superseded version in any provider's
`chat.md` -- numbered ones you can jump to, and chatgpt's, which you can only
be told about.

## Other things you can do

Re-render from bytes already captured (no browser, no network):

```bash
chatfs-provider-claude-conversation-url-render --cache ~/chats https://claude.ai/chat/$UUID
```

Pull many conversations — capture the sidebar index first, which lays down a
chat dir per conversation, then walk them (the commands below take a path
instead of `--cache`; the path says both which cache and which provider):

```bash
chatfs-provider-claude-index --cache ~/chats
chatfs-conversation-path-browse ~/chats/claude/.chat/$UUID/
chatfs-conversation-path-render ~/chats/claude/.chat/$UUID/
```

Listing an index is per-provider — it's one account's sidebar — but the walk
is not: the chat dir's own path says which provider it belongs to, so a
mixed stream of chat dirs walks with one command.

The index command reports what it placed, one JSON object per chat —
`{id, title, chat_dir, view, updated}` — so you can drive the walk from it
instead of filling in `$UUID` by hand:

```bash
chatfs-provider-claude-index --cache ~/chats |
  jq -r .chat_dir |
  xargs -rL1 chatfs-conversation-path-browse
```

`chatfs-provider-claude-index` is the two index stages joined for you. Run them
apart when you want to see or filter the pages in between — the browse
stage emits one raw index page per line on stdout, which is large (most
of it is per-conversation feature-flag settings), so pipe it somewhere
rather than to a terminal:

```bash
chatfs-provider-claude-index-browse --cache ~/chats | chatfs-provider-claude-index-splat --cache ~/chats
chatfs-provider-claude-index-browse --cache ~/chats | jq -c '.data[] | {uuid, name, created_at}'
```

Pull everything that changed recently — index each provider, then walk
only the conversations that are both recent and out of date:

```bash
chatfs-refresh --cache ~/chats 7
```

or one provider at a time:

```bash
chatfs-provider-claude-refresh --cache ~/chats 7
```

The number is days. Every capture still waits for **Done Capturing** —
refresh decides which conversations are worth opening, it doesn't click
for you. A conversation whose captured `conversation.json` is newer than
the provider's own last-modified timestamp is skipped without opening
anything; `DEBUG=1` names each skip. Conversations the provider listed
*without* a last-modified timestamp are skipped too, and those you're
told about whether you asked or not:

```
3 record(s) carried no timestamp and were skipped
```

If the captured index doesn't reach back that far, refresh stops
*before* opening any conversation and prints the date to scroll back
to — nothing scrolls the sidebar for you yet, so an index that stops
short would otherwise mean a silently partial refresh. Re-run with the
sidebar scrolled past that date. Exit status 3 means exactly that;
other non-zero statuses mean a capture failed, and the failing chat is
named on stderr.

Throw one away — moves the chat dir and its symlinks to the provider root's
own `trash/`:

```bash
chatfs-provider-claude-conversation-url-trash --cache ~/chats https://claude.ai/chat/$UUID
```

The repo carries captured fixtures at
`docs/dev/design-incubators/chatfs-cli-mockup/chatfs.demo/<provider>` — point
`--cache` at `chatfs.demo` to try the render stages without capturing
anything; the `<provider>` segment is appended for you.

## When it goes wrong

Every stage rebuilds its output from scratch, so **re-running is always safe**
and is the first thing to try.

The raw capture stays on disk at `.chat/$UUID/.data/` — `cdp.jsonl` (the
browser's network traffic) and `conversation.json` (the provider's own
conversation document, extracted from it). A failure leaves those in place
to look at, and the previous successful capture is never destroyed by a
failed one.

**"no sidebar index page included $UUID"** — capturing by URL relies on the
page also loading your conversation list, which is where the title and
timestamp come from. If it didn't, run the bulk path above instead:
`chatfs-provider-<provider>-index`, then `path-browse`.

**"capture holds only N of this conversation's pages"** -- chatgpt sends
older messages only as you scroll back through them, so a capture taken
from the bottom of a long conversation has a prefix missing. Scroll to the
top of the conversation, then click **Done Capturing**. The previous
`conversation.json` survives the failure, so re-running costs only the
browse.

**Capture succeeded but the conversation isn't in it** — providers may serve
a revisit from their own client-side cache and never hit the network. Local
storage is cleared before navigating to prevent exactly this; if you opted
out with `har-browse --keep-origin-storage`, don't.

## Deeper

- Stage-by-stage walkthrough, and why the layout is shaped this way:
  [packages/chatfs-cli/README.md]
- Where all this is headed: [../README.md]
- The design knowledge behind it: [dev/design.kb/]

[packages/chatfs-cli/README.md]: ../packages/chatfs-cli/README.md
[../README.md]: ../README.md
[dev/design.kb/]: dev/design.kb/
