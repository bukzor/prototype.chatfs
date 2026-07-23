# Possess Your Own Conversation Data

chatfs renders conversations that live inside chat providers
(claude.ai, chatgpt.com). Everything downstream — extraction,
rendering, the filesystem — presumes the raw data is already in hand.
The capture stage (BB1) exists to make that true.

## The Problem

The data is yours, but you don't hold it. Official exports and APIs
are lossy exactly where chatfs cares most: fork/tree structure and
whatever tomorrow's features turn out to need are what they drop or
never expose. The one complete, always-available source is the traffic
the provider already sends your own browser during ordinary
authenticated use.

## Who Benefits

The chatfs user: their conversations become durable local artifacts,
independent of provider retention, export formats, and API access.

## What Success Looks Like

After an ordinary human browsing session, the user durably possesses
raw captured data sufficient for chatfs extraction — including for
needs unknown at capture time. A years-old capture still yields data
to a new extractor, with no recapture. Nothing the user saw on screen
is missing from the archive.
