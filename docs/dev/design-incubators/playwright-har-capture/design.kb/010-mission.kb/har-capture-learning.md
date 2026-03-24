# Learn Browser-Driven HAR Capture

BB1 (capture) is the foundation of the chatfs pipeline — everything downstream
(extract, emit, cache, filesystem) depends on artifacts it produces. But we have
zero experience with Playwright's HAR recording, browser lifecycle management,
network idle detection, or content encoding handling.

## The Problem

chatgpt-splat can process existing HAR files (BB2/BB3), but nobody has built
the piece that *generates* them. Browser automation for HAR capture involves:

- Launching and controlling a real browser instance
- Intercepting and recording network traffic
- Detecting when relevant requests have completed
- Handling compressed responses (gzip, brotli) in HAR format
- Cleanly finalizing the HAR on exit

These are skills we need but don't have. Learning on a production target
(claude.ai, chat.openai.com) conflates learning Playwright mechanics with
navigating authentication, Cloudflare, and ToS questions.

## Who Benefits

The chatfs developer (user). This subproject de-risks BB1 by isolating the
"how does Playwright HAR capture actually work?" question from all
provider-specific concerns.

## What Success Looks Like

After completing this subproject, the developer can confidently write a
Playwright capture script for any target because they understand:

- HAR recording lifecycle (start, populate, finalize)
- How to trigger and wait for specific network activity
- How HAR represents compressed/encoded responses
- The "capture → extract → emit" pipeline shape as a CLI tool
- Failure modes and how to handle them

The toy components (server, capture script, plucker, emitter) are reusable
as test fixtures and reference implementations for the real BB1.
