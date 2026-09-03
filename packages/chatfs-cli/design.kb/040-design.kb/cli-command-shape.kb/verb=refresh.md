# verb=refresh

`refresh` brings a provider's local cache up to date with what the
account holds: run the index, then browse the conversations that are
both recent and stale. It is the bulk counterpart to
`conversation url browse` -- same capture, chosen for you rather than
named by you.

## Commands

- `provider <name> refresh <days>` -- run that provider's `index`, keep
  the chats updated within the window, browse the ones whose local
  capture is older than the provider's own `updated` timestamp.
- `refresh <days>` -- the same, over every provider in turn.

Both remain human-driven: each browse opens a window and waits for
**Done Capturing**. What refresh removes is the bookkeeping -- deciding
which chats are worth a click -- not the clicking.

## A verb with no noun

The scheme is noun-then-verb, and `refresh` breaks it: its object is
the provider's whole cache, not one artifact the pipeline manipulates.
Spelling it `provider claude cache refresh` would coin a `cache` noun
no other command takes, to restore a symmetry no reader was missing.
The `provider` partition is the object here, and a verb applied
directly to it reads correctly: *refresh the claude provider*.

## Why the bare name fans out instead of dispatching

A dispatching form (`conversation url browse`) reads the provider off
the *address* it was handed. `refresh` takes a number of days and no
address, so there is nothing to dispatch on. `chatfs-refresh` therefore
means "every provider, in turn" -- a fan-out driver, not a dispatcher.
The distinction is worth keeping straight: an address-less command
cannot dispatch, but it can still have a shortest-name form that
finishes the job.

Fan-out does not stop at the first failure. A provider whose index came
up short must not cost the other two their refresh; the driver reports
each provider's outcome and exits non-zero if any failed.

## The skip rule

A chat is browsed when the index says it changed after the local
capture was taken:

    captured is missing, or captured < updated

`captured` is the mtime of `.data/$UUID/conversation.json`, which is
written by exactly one stage and atomically promoted only on a
successful capture -- so its mtime is that capture's completion time,
not a partial attempt's.

Unknown `updated` -- a provider payload that omits the field -- is not
recent, so the window filter drops it before staleness is ever asked.
An absent timestamp is no evidence of recency, and the alternative
reading (unknown means refresh it) would open a window for every such
chat, which is the one failure an attended tool cannot afford. The
silence that reading was meant to prevent is bought back cheaply
instead: the count of timestamp-less records is reported on stderr
whether or not anyone asked for debug output, and an index where *no*
record carries a timestamp fails the coverage check outright.

Two limits are accepted rather than solved. A local clock running ahead
of the provider's can skip a change that landed inside the skew; the
skew is seconds and the edit it would hide is human-paced, so the risk
is small and a wider window re-checks it. And a cache copied without
preserving mtimes reads as entirely fresh -- `cp -ar` preserves them,
plain `cp` does not.

Rejected: recording the watermark in `meta.json`. The index splat
rewrites `meta.json` from the fresh index item *before* anything reads
it back, so the previous value is gone at exactly the moment the
decision needs it. A dedicated stamp file beside `conversation.json`
would work and is the upgrade path if mtime proves untrustworthy; it
buys nothing today.

## Coverage is checked before any conversation is browsed

A captured index is only as complete as the sidebar the browser
actually loaded, and pagination past the first page is not yet driven
(the `has_more` gap tracked in the package taskfile). So "the last N
days" is a claim the capture has to earn: at least one indexed chat
must be *older* than the cutoff, which is what proves the index reached
past the window's edge.

When it doesn't, the command fails before opening a single
conversation, naming the date to scroll back to. Failing afterward
would spend the operator's whole attention budget to buy a set that was
incomplete from the start.
