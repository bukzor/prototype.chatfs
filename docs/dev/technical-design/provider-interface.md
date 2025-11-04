# Claude.ai Unofficial API Reference

**Last Updated:** 2025-11-01

**Status:** 📝 Reference doc - Will be populated during Milestone 0 (design phase)

This document will serve as the canonical reference for the unofficial claude.ai
API as exposed by st1vms/unofficial-claude-api.

**Read this when:**

- Implementing API client wrapper (during M1-CLAUDE)
- Debugging API issues
- Understanding conversation data structures
- Investigating fork representation

**To populate during M0-DOCS:**

1. Make real API calls using st1vms/unofficial-claude-api
2. Document actual request/response formats
3. Investigate fork representation in API responses
4. Document authentication mechanism
5. Replace TBD placeholders with real data

## API Client Library

**Repository:** https://github.com/st1vms/unofficial-claude-api (Python)

**Why this one:**

- Uses curl_cffi for Cloudflare TLS fingerprinting bypass
- Most recent working implementation (last push June 2025)
- 181 stars (community-vetted)
- Full conversation access API

**Installation:**

```bash
# Vendored in unofficial-claude-api/ subdirectory
# Uses session key from claude.ai cookies
```

## Authentication

**Session Key:**

- Obtained from claude.ai browser cookies
- Cookie name: `sessionKey`
- Format: `sk-ant-...`
- Stored in `.env` file: `CLAUDE_SESSION_KEY=sk-ant-...`

**How to get:**

1. Log into claude.ai in browser
2. Open DevTools → Application → Cookies
3. Copy `sessionKey` value
4. Store in `.env` or environment variable

## API Endpoints

**Note:** These are inferred from unofficial-claude-api library. Need to verify
with real calls.

### List Organizations

**Client method:** `client.list_organizations()`

**Request:** (TBD - investigate)

**Response:** (TBD - investigate)

**Expected fields:**

```json
{
  "uuid": "6e56e06e-6669-4537-a77c-ae62b3d3c221",
  "name": "Buck Evan",
  "created_at": "2025-10-15T10:00:00Z"
}
```

**Questions:**

- What's the exact HTTP request?
- Any pagination for orgs?
- Other metadata fields?

### List Conversations

**Client method:** `client.list_conversations(org_uuid="...")`

**Request:** (TBD - investigate)

**Response:** (TBD - investigate)

**Expected fields:**

```json
{
  "uuid": "7ddc2006-e624-4fb6-ba88-b642827a2606",
  "title": "Tshark HTTP request filtering",
  "created_at": "2025-10-29T13:33:33Z",
  "updated_at": "2025-10-29T13:33:42Z",
  "org_uuid": "6e56e06e-6669-4537-a77c-ae62b3d3c221",
  "message_count": 4
}
```

**Questions:**

- Pagination? (likely yes for 100s of conversations)
- Date filtering options?
- How are forked conversations represented?
  - Same UUID as parent with branch ID?
  - Separate UUIDs with parent_uuid field?
  - Ancestry chain?

### Get Conversation

**Client method:** `client.get_conversation(convo_uuid="...")`

**Request:** (TBD - investigate)

**Response:** (TBD - investigate)

**Expected message structure:**

```json
{
  "type": "human",
  "text": "How do I filter tshark to show only HTTP requests?",
  "created_at": "2025-10-29T13:33:33Z",
  "uuid": "msg-123"
}
```

**Critical questions for fork representation:**

- Do messages include parent_uuid or fork_point?
- Is there an ancestry field?
- How are forked branches identified?
- Can we list all forks from a parent conversation?

## Fork Representation

**Status:** Under investigation in
[../../../design-incubators/fork-representation/]

Key unknowns: How does the API represent forks? Are they separate conversations
or branches within one conversation?

This will be documented here once the investigation is complete and real API
data is available.

## Data Structures

### Organization

**Fields:** (TBD - verify with real API call)

- `uuid` (string) - Unique identifier
- `name` (string) - Display name
- `created_at` (ISO 8601 datetime)
- Other fields?

### Conversation

**Fields:** (TBD - verify with real API call)

- `uuid` (string) - Unique identifier
- `title` (string) - Conversation title
- `created_at` (ISO 8601 datetime)
- `updated_at` (ISO 8601 datetime)
- `org_uuid` (string) - Parent organization
- `message_count` (integer)
- Fork-related fields? (unknown)

### Message

**Fields:** (TBD - verify with real API call)

- `type` ("human" | "assistant")
- `text` (string) - Message content
- `created_at` (ISO 8601 datetime)
- `uuid` (string) - Message identifier
- Attachments? Files? Images?

## Error Handling

**Questions:**

- What HTTP status codes for auth failure?
- Rate limiting?
- Malformed request errors?

**Need to test:**

- Invalid session key
- Non-existent conversation UUID
- Network errors

## Known Limitations

From st1vms/unofficial-claude-api:

- Uses Cloudflare bypass (curl_cffi)
- May break if claude.ai changes TLS fingerprinting
- Unmaintained (last push June 2025)
- No official support or guarantees

## Investigation TODO

**High priority:**

1. [ ] Document actual list_organizations() request/response
2. [ ] Document actual list_conversations() request/response
3. [ ] Document actual get_conversation() request/response
4. [ ] **Investigate fork representation in API** (critical for write
       operations)

**Medium priority:** 5. [ ] Document pagination for conversations 6. [ ]
Document error responses 7. [ ] Test rate limiting behavior 8. [ ] Document
message attachments (if any)

**Low priority:** 9. [ ] Document all org metadata fields 10. [ ] Document all
conversation metadata fields 11. [ ] Document all message metadata fields

## Related Documents

- [../technical-design.md] - How we wrap this API
- [../../../design-incubators/fork-representation/] -
  Fork design exploration
- [../design-rationale.md#unofficial-api-instead-of-official] -
  Why unofficial API
