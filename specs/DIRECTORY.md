# CHG-003 shared directory and recipient acknowledgments

This explicitly registered shared extension is authoritative for CHG-003 and overrides only the baseline clauses identified below. It adds routes under /api/v1 without changing the version-1 health, Send, Receipt, Message, Page, outbox state or storage schemas. Old clients continue to message but cannot report durable receipt; their unacknowledged accepted messages remain queued in server management. Both current clients must be regenerated to implement this extension.

## Meanings and ownership

User choice (USER_EXPLICIT): “Show server-accepted messages awaiting recipient acknowledgment as queued; label offline client queues as unknown.” Server management is observational only. Received means the recipient reported durable local storage, not that a human read a message. An acknowledgment is an unauthenticated claim under the existing local-demo trust model, not proof of identity. Do not add read receipts, registration prerequisites, account administration, force delivery, or collection of client outbox snapshots.

A server session knows usernames from a successful announcement, accepted message sender/recipient, or valid receipt report. Directory membership does not expire within the session. Recent presence is advisory: online=true only when a successful explicit announcement occurred less than 15 monotonic seconds ago. Sends, GETs, acknowledgments, or the operator's refresh do not renew presence. Never-announced/addressed users are listed with online=false. Closing/disconnecting a client leaves it listed; its recent-presence flag eventually expires. Clients can select offline users. A valid manually typed recipient need not be listed or announced. Directory/receipt state is in memory and clears on every new server instance, like messages.

## Exact wire additions

All baseline JSON, framing, content type, size, duplicate-member, redirect, body deadline, and loopback rules apply. New Error fields are username and through in addition to existing fields. New code INVALID_RECEIPT maps to HTTP 400, field through. Never alter legacy message or health response keys.

### POST /api/v1/users

No query. Exactly {"username":"alice"}, validated with the same username grammar. Wrong fields/type: INVALID_FIELDS, null; invalid username: INVALID_USERNAME, username. Under the store lock create/update one directory entry and mark its announcement time. Return 200 exactly {"username":"alice"}. Repeated announcement is idempotent membership refresh, not account creation/authentication. It does not reset messages, cursors or receipt progress.

### GET /api/v1/users

No query or nonempty request body. Return 200 exactly {"users":[{"username":"alice","online":true},{"username":"bob","online":false}]}. Users are unique and lexicographically ordered by username; each row has exactly username and boolean online. Return an empty array for a new session. Compute presence on each observation. No messages or client outbox contents are returned.

### POST /api/v1/receipts

No query. Exactly {"recipient":"bob","through":3}. Validate fields, recipient, then through. through is an exactly integral JSON number 0–9007199254740991; booleans are invalid. Bad recipient: INVALID_USERNAME, recipient. Invalid through: INVALID_RECEIPT, through. If through exceeds this recipient's current highest accepted sequence, reject with 409 CURSOR_INVALID, through, without changing any state.

Within the same lock as sends/reads, remember max(previous acknowledgment, through) for the recipient. Return 200 exactly {"recipient":"bob","through":3} using that monotonic maximum. Duplicate, concurrent, and older reports cannot regress progress or allocate/delete messages. GET message retrieval never acknowledges receipt. Acknowledgments do not alter original acceptance receipts or sender outbox state. A report through 0 is valid for an empty stream. Acknowledgments are cumulative because incoming sequences are contiguous.

After client reset, an acknowledgment response may be ahead of the new local cursor because the server remembers an earlier report. Validate response recipient and a safe integer through >= requested through, but NEVER copy its through into the local receive cursor or skip fetching messages. Receipt reports describe a past durable commit; local reset does not revoke them. Server restart clears them. Unknown methods on users allow GET, POST; on receipts allow POST only. Query/body/error handling follows the existing route ordering.

## Client scheduling, durability and failure isolation

This section deliberately extends the baseline two-request synchronization cycle. Keep one serialized scheduler, one earliest queued send followed by one incoming GET, preserving all old messaging behavior. After this messaging work, if still online, not paused, not closing/resetting, perform in order: POST the current durable receive cursor to receipts; POST the current identity to users; GET users. Each new-route request has a total two-second deadline including its body (legacy message requests retain five seconds). Then wait the existing one-second delay. A normal cycle is bounded by 16 seconds of network work plus local work. Do not overlap requests/cycles or create a second directory polling worker. Announcement begins after local identity commit and also occurs after stored-identity startup/reconnect, via this cycle; identity creation/offline enqueue never depend on server availability.

Only acknowledge a cursor read from committed metadata. Validate/commit the entire incoming page and cursor atomically BEFORE submitting that cursor. Failed/malformed page or failed commit must never acknowledge beyond the previous durable cursor. Resend the durable cursor every cycle, including empty-page cycles and after restart; no additional persistent acknowledgment schema is required. Lost/rejected/malformed acknowledgment responses leave local inbox/cursor/outbox intact and retry later. Missing directory/receipt endpoints on an older server produce separate feature errors, not loss of core messaging. Auxiliary failures never fail or dequeue a message, pause synchronization, overwrite outbox errors, or hide a messaging error. A message GET's valid CURSOR_INVALID still pauses all requests until reset. Development offline mode blocks new requests on ALL routes. Enqueue while intentionally offline must not mutate persisted outbox error fields just because auxiliary work is blocked.

Validate exact announcement response, exact directory shape/row keys/types/sorted unique names, and exact acknowledgment response. Keep the last valid directory after a bad response or transport failure, mark it stale/error, and recover on later valid responses. Cache is process/page-local only. No server/user directory data or ack bookkeeping is added to SQLite/IndexedDB version 1. Clearing/resetting identity clears cached directory and receipt observations. All new route responses carry the same identity/reset generation guard as messages; stale replies cannot restore old UI/store state. Show login only AFTER reset completion, cleared message rows and enabled login controls render together; app.ready must reflect this readiness.

## Client GUI controls

Add a visible known-recipient list, case-insensitive local substring filter, and Refresh. Exclude the current user from the selectable list. Directory selection sets recipient-input to the exact username, preserving the draft; it never automatically sends. Keep manual recipient entry and the existing Send behavior. Label presence as “recently seen” / “not recently seen”, not guaranteed reachability. Refresh schedules/coalesces the normal cycle; no concurrent worker. Preserve list selection and composition while refreshing. Offline use keeps last-known recipients with directory-status=stale; initial unobserved directory is empty/loading (or stale if offline). Errors remain visible in separate feature status, without overwriting baseline validation/synchronization errors. A valid directory response updates the cache; status=current requires both announcement and directory fetch success in that cycle. Announcement or directory HTTP/schema failure sets error; transport failure or explicit offline sets stale, even if an in-flight successful response arrives afterward. The receipt-status observation is unknown initially, confirmed after valid report response, error on report failure, pending when newly committed receive progress has not yet been reported; it is neither an outgoing-message delivery flag nor a read receipt.

Python app.widgets additions:
- user-filter: Entry/ttk.Entry; KeyRelease applies the local filter.
- user-refresh: Button/ttk.Button.
- user-directory: ttk.Treeview, iid=username, values=(username,presence); TreeviewSelect selects the recipient.
- directory-status: Label text loading/current/stale/error; a separate explanatory label may give details.
- receipt-status: Label text unknown/pending/confirmed/error; separate explanation is allowed.
All previous widgets and machine commands/schemas remain unchanged. Machine mode runs the same receipt/directory scheduler, without requiring Tk.

Browser data-testid additions:
- user-filter input; user-refresh button; directory-status text loading/current/stale/error.
- user-directory container; user-item buttons with data-username, user-name and user-presence descendants. Click uses the production recipient-selection handler.
- receipt-status text unknown/pending/confirmed/error.
Use exact text, not HTML injection. Keep prior selectors, layout tasks, error handling, and storage semantics.

## Server management controls

Preserve the existing overview and lifecycle controls. Add a Users tab with the same directory (including every known user), local substring filter, Refresh, and selected username. Operator refresh is a read-only snapshot, never an announcement or acknowledgment. Display per-user Sent (all accepted outgoing), Received (incoming with sequence <= acknowledged through), and Queued (incoming above that acknowledgment) views. Sent rows indicate queued or received according to the recipient's acknowledgment; a user can therefore inspect pending outgoing messages in Sent and pending incoming in Queued. All per-user messages remain inspectable using scrollable lists; the old global Overview remains latest-200. Selection preserves exact multiline details. The user directory, activity categories, counts and receipt classification must come from one locked store observation; do not derive acknowledgment from a GET, open window, online presence, or operator action.

Server app.widgets additions:
- server-tabs: ttk.Notebook with Overview and Users tabs; activity-tabs: ttk.Notebook with Sent, Received, Queued tabs.
- user-filter Entry (KeyRelease filters); user-refresh Button; users Treeview iid=username, values=(username,presence); directory-status Label current/stopped. The server presence column is titled Status with Online/Offline values from the existing boolean, as specified in SERVER.md; a presence-notice Label explains the 15-second heartbeat timeout. Client presence wording remains as specified above.
- selected-user Label exact username or empty; user-sent-count, user-received-count, user-queued-count numeric Labels.
- user-sent, user-received, user-queued Treeviews: iid=sender+":"+message_id, values=(peer,message_id,sequence,state,text). peer is recipient for Sent and sender otherwise; state is queued/received.
- user-message-detail readonly Text: selection in any activity table shows exact text.
- queue-notice Label must explicitly explain “Offline client queues: unknown”, recipient acknowledgment and no read confirmation.
Stop/Start clears users, selection, lists and counts along with old monitoring. Remove a filtered-out selection and clear its details rather than showing stale/unrelated activity. Existing controls/default Overview remain compatible. Refresh/selection/filtering must not mutate delivery state. No editing/deleting/renaming/banning controls are added.
