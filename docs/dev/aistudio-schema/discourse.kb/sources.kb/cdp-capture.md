---
kind: dataset
title: "aistudio.cdp.jsonl — CDP network capture"
url: "../../design-incubators/chatfs-cli-mockup/aistudio.cdp.jsonl"
tags: [aistudio, capture, cdp]
---

The raw input to the pipeline: a Chrome DevTools Protocol network capture
whose `Network.responseReceived` events carry response bodies for the
`boq-makersuite` JS modules. JSONL form, one CDP event per line.
