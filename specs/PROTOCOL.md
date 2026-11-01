# Messaging protocol version 1

Status: current wire and synchronization contract, implemented by the server and generated clients. This specializes [PRODUCT.md](PRODUCT.md).

## Transport and address

Use HTTP/1.1 with JSON over a loopback origin. Default origin: `http://127.0.0.1:8765`. The server binds to `127.0.0.1`; tests may select port 0 and use the actual announced port. Python accepts a configurable HTTP loopback origin with no credentials, path, query, or fragment. Browser API calls use the page's origin. No cross-origin API support is required; do not add permissive CORS. Clients reject redirects and bypass environment HTTP proxies for local traffic.

API requests/responses use UTF-8 `application/json`, optionally `charset=utf-8` (case-insensitive media type/charset). No other charset or content encoding is supported. Encode JSON as UTF-8 without BOM. Ignore JSON object member order; reject nonfinite numeric tokens, malformed UTF-8/JSON, and unknown fields in declared objects. The server rejects duplicate request members; all producers emit unique members. Clients may use ordinary JSON parsing for responses and need not implement duplicate-member detection, but must validate the parsed schemas and values. Integers must be JSON numbers with an exact integral value in the specified range; booleans are not numbers. Text is Unicode scalar data; no normalization. API responses include `Content-Length` and `Cache-Control: no-store`.

The server accepts at most 32,768 request-body bytes. POST requires one nonnegative decimal Content-Length and JSON content type. Missing length, invalid/conflicting length headers, or Transfer-Encoding yields INVALID_REQUEST. An over-limit declared/read body yields PAYLOAD_TOO_LARGE. Bound body reading to five seconds; an incomplete/timed-out body yields INVALID_REQUEST and closes the connection where a response is possible. Unsupported Content-Encoding or media type yields UNSUPPORTED_MEDIA_TYPE. Do not commit a partially read request.

## Primitive values and exact objects

| Name | Contract |
|---|---|
| Username | String, full ASCII match `[a-z][a-z0-9_]{0,31}`. No trim, case folding, or Unicode normalization. |
| Message ID | Canonical lowercase hexadecimal UUID string, groups 8-4-4-4-12. Clients create UUIDv4 using a cryptographically appropriate runtime generator. The server accepts any canonical UUID bit pattern. |
| Text | Nonempty scalar Unicode string, at most 4,096 UTF-8 bytes. Preserve all whitespace/newlines. |
| Sequence | Integer 1 through 9,007,199,254,740,991 inclusive. Assigned only by the server, independently per recipient. |
| Cursor | Integer 0 through 9,007,199,254,740,991 inclusive. Zero precedes the first incoming message. |
| Send | Exactly `message_id`, `sender`, `recipient`, `text`, using the types above. Sender differs from recipient. |
| Receipt | Exactly `message_id`, `sender`, `recipient`, `sequence`. No text or timestamp. |
| Message | Exactly the Send fields plus `sequence`. |
| Page | Exactly `messages` (array of 0–100 Message objects) and `next_after` (Cursor). |
| Error | Exactly `error`, whose object has exactly `code` (one code below), `message` (nonempty English string), `field` (null or a field name below). Error prose is not stable; tests assert code/field/status. |

Error fields are `message_id`, `sender`, `recipient`, `text`, `after`, or null. Error messages contain no credentials or internal traceback.

The 32,768-byte limit applies to request bodies, not receive pages. A valid page containing 100 texts of 4,096 control characters expands to approximately 2.47 MB when JSON-escaped by this server. Clients must accept every maximum-size page the server can emit; if imposing a response-buffer cap, allow at least 4 MiB. Validate the decoded message count and text-byte limits independently.

## Routes

### GET /health

No query parameters or request body. Return 200 and exactly `{"status":"ok","protocol_version":1}`. This is readiness, not proof that client generation or end-to-end delivery works.

### POST /api/v1/messages

No query parameters. Validate framing/media/JSON, exact fields, message_id, sender, recipient, self-send, and text in that order. A recipient need not exist as a client. Under one shared server lock, look up `(sender,message_id)` and then accept:

- New key: append the immutable payload to the recipient's stream, assign its next contiguous sequence starting at 1, retain a receipt and the full original payload, return 201 with Receipt.
- Existing key and identical recipient/text: return 200 with the original Receipt. Allocate nothing and append nothing.
- Existing key with changed recipient/text: return 409 IDEMPOTENCY_CONFLICT; neither the original message nor its receipt changes.
- Same message_id under another sender is a distinct key. A sequence allocator at its maximum rejects new messages with 503 SEQUENCE_EXHAUSTED; exact retries still work.

The lock makes concurrent exact requests produce one acceptance. Commit in memory before writing the HTTP response. Disconnecting after acceptance does not undo acceptance. Never delete accepted messages on retrieval in this version.

Example new send and receipt:

```json
{"message_id":"11111111-1111-4111-8111-111111111111","sender":"alice","recipient":"bob","text":"Hi Bob, I have something important to tell you"}
```

```json
{"message_id":"11111111-1111-4111-8111-111111111111","sender":"alice","recipient":"bob","sequence":1}
```

### GET /api/v1/messages?recipient=bob&after=0

Require exactly one `recipient` and one `after`; reject missing, repeated, or unknown query keys. Decode URL encoding strictly. `after` is canonical unsigned ASCII decimal (`0` or a nonzero digit followed by digits); reject signs, spaces, decimals, leading zeros, and unsafe integers. No request body is allowed. Validate recipient before after. Use INVALID_USERNAME for recipient and INVALID_QUERY for malformed query/cursor syntax. If after exceeds this recipient's current highest sequence (zero for an empty stream), return 409 CURSOR_INVALID.

Under the same store lock, return at most the first 100 messages with sequence greater than after, ordered ascending and contiguous from after+1. `next_after` is the last sequence, or unchanged after for an empty page. A response is a stable snapshot; subsequent requests may see newly accepted messages. Return an empty page for a valid never-launched recipient whose stream is empty.

```json
{"messages":[{"message_id":"11111111-1111-4111-8111-111111111111","sender":"alice","recipient":"bob","text":"Hi Bob, I have something important to tell you","sequence":1}],"next_after":1}
```

There is no separate recipient acknowledgment endpoint; GET does not imply receipt was durably stored.

### Other requests and static assets

Known API routes with unsupported methods return 405 METHOD_NOT_ALLOWED and Allow. Unknown `/api/` paths return 404 NOT_FOUND. Route/query checks precede reading a POST body. GET /health with a query returns 400 INVALID_QUERY. Reject nonempty bodies on GET API/health requests with 400 INVALID_REQUEST.

Serve browser assets from a configured local build directory; `/` maps to `index.html`. Allow GET/HEAD only for static resources. Return appropriate HTML/CSS/JavaScript MIME types and no-store caching. Normalize/resolve paths and reject traversal or symlink escapes outside that directory. A missing static file returns 404. Static error bodies may be plain text; API errors use Error. No directory listing, runtime CDN, SPA route fallback, or service worker is required. API service can start before assets exist.

## Error mapping

| HTTP | Code | Field / meaning |
|---|---|---|
| 400 | INVALID_REQUEST | null; framing, forbidden body, or incomplete body |
| 400 | INVALID_JSON | null; invalid UTF-8/JSON, duplicate members, nonfinite token |
| 400 | INVALID_FIELDS | null; wrong outer type, missing/unknown members |
| 400 | INVALID_MESSAGE_ID | message_id |
| 400 | INVALID_USERNAME | sender or recipient |
| 400 | SELF_SEND | recipient |
| 400 | INVALID_TEXT | text |
| 400 | INVALID_QUERY | after for an invalid after value; otherwise null |
| 404 | NOT_FOUND | null |
| 405 | METHOD_NOT_ALLOWED | null |
| 409 | IDEMPOTENCY_CONFLICT | message_id |
| 409 | CURSOR_INVALID | after; cursor is beyond this server stream |
| 413 | PAYLOAD_TOO_LARGE | null |
| 415 | UNSUPPORTED_MEDIA_TYPE | null |
| 503 | SEQUENCE_EXHAUSTED | null |
| 500 | INTERNAL_ERROR | null; unexpected server failure |

```json
{"error":{"code":"SELF_SEND","message":"Choose a different recipient.","field":"recipient"}}
```

## Durable enqueue and outgoing state machine

Before networking, atomically allocate local order, generate a previously unused local ID, insert the queued payload, and advance the order allocator. A local ID collision retries UUID creation before commit; an exhausted allocator fails visibly. After commit the payload and ID are immutable. A 409 network conflict must not silently generate a replacement ID.

| Attempt outcome | Durable outcome |
|---|---|
| 200/201 with JSON Receipt, matching all three submitted identity/address fields and a valid sequence | accepted with that sequence; never send this entry again |
| Connection failure, five-second total deadline, HTTP 408/429/5xx | queued with an actionable error; retry the same payload |
| Other HTTP 4xx, even with a malformed/non-JSON error body | failed; use the valid Error when available, otherwise a local HTTP_ERROR explanation |
| Redirect, other HTTP status, wrong content type, malformed success JSON, mismatched/invalid Receipt | queued; PROTOCOL_ERROR when distinguishable, because acceptance is uncertain. Browser fetch with redirect:error may expose a redirect only as TypeError; TRANSPORT_ERROR is allowed for that indistinguishable failure. |
| Failure to commit accepted/failed state | Preserve the last committed queued record; report STORAGE_UNAVAILABLE and permit idempotent retry |

No queued item is dropped for retry count. Failed rows are retained and excluded from future sends; the user can submit a new message as a new ID. A response body/content-type failure must not obscure a known permanent HTTP 4xx status. Local validation never consumes a message ID/order in durable storage.

## Synchronization and incoming validation

At startup with a stored identity, successful first login, explicit reconnect, browser online/focus/visibility activation: schedule an immediate cycle. Merge overlapping triggers into one worker. Otherwise wait one second after a completed cycle; no concurrent cycles or overlapping requests. A cycle sends at most the earliest queued entry then fetches one incoming page, even if the send failed. One cycle may therefore take up to ten seconds plus local work. Five seconds is the complete request deadline, including response body; cancel/close requests on expiry. Backoff is the fixed one-second delay, with no jitter or unbounded exponential delay in v1.

Validate Page content type, exact schemas, safe integers, valid usernames/IDs/text, recipient equal to the current identity, distinct sender, no repeated message keys, contiguous sequences beginning at requested after+1, and matching next_after. Validate before storage, then in one transaction compare/insert deduplicated inbox rows and update the cursor. Existing identical `(sender,message_id)` rows may be retained; any conflicting payload/sequence or duplicate sequence mapped to another key rejects and rolls back the entire page. A repeated stale page cannot advance the cursor. Read the persisted cursor again next cycle.

Malformed pages, GET transport/errors other than a valid 409 CURSOR_INVALID, or aborted writes leave inbox/cursor unchanged and allow later retries. A valid CURSOR_INVALID pauses both sending and receiving and prominently requests explicit reset. Toggling online mode does not clear this pause. Do not infer a fresh session from empty results or automatically clear storage.

Development offline mode blocks new requests before dispatch, while enqueue and snapshots continue. An in-flight request may already have reached the server; its uncertainty uses normal retry/deduplication behavior. External faults must exercise that same path. Only explicit reset invalidates all old asynchronous responses; a reset completion must not be followed by a stale write.

Server process restart discards all streams, receipts, and counters. Even when an old cursor happens to be numerically valid on a new server, this version cannot reconcile sessions. A fresh server session requires explicit fresh/reset client stores. There is no cross-session delivery guarantee.
