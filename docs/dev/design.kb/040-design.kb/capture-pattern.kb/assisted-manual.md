# Assisted Manual Capture

Inject a wizard UI that guides the user through a manual capture sequence:
"click this refresh button," "now save the HAR file from DevTools," etc.
Detects events (refresh fired, HAR saved) and advances the wizard.

**Pros.** Maximum policy safety — the automation never touches provider APIs
directly, only coaches the user through the standard browser feature set.
Graceful degradation when injected UI or network capture fails.

**Cons.** Worst UX of the five — user has to follow steps every time. Only
attractive if the other patterns become infeasible (e.g. provider aggressively
blocks automation-detected contexts).
