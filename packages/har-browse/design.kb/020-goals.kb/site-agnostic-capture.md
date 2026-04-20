---
why:
  - reusable-capture-components
---

# Site-Agnostic Capture

The capture harness should be fully site-agnostic. The only parameter is the
URL. All site-specific interaction (login, 2FA, captcha, navigation, scrolling)
is performed by the human operator during the capture session. The harness
records everything and waits for the human to signal completion.

This means the capture tool works against any website without code changes —
the same script captures from a toy localhost server, claude.ai, or
chat.openai.com.
