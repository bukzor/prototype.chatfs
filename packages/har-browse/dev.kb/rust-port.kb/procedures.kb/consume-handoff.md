# Consume a hand-off

When you read a `handoffs.kb/$topic.md` and act on it.

## Steps

1. Read the file.
2. Apply the implied work or factor it into the current commit.
3. **Decide:** durable knowledge or transient note?
   - **Durable** = you'd cite it in a future bug report or architecture discussion. → Promote: write a long-lived doc in `dev.kb/` (or update an existing one), *then* delete the hand-off.
   - **Transient** = useful only across this hand-off, no future cite value. → Delete the hand-off.
4. Never leave a consumed hand-off in place. Stale hand-off ≈ bug.

## Trigger

About to act on the contents of a hand-off file, or finished acting on it.
