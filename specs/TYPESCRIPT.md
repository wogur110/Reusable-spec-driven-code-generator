# TypeScript browser client contract

Status: current implemented browser contract; builds and baseline browser checks pass. Shared behavior is defined by [PRODUCT.md](PRODUCT.md) and [PROTOCOL.md](PROTOCOL.md).

## Source, build, and origin

Generated boundary: `generated/typescript-web/`. Required source: `index.html`, `styles.css`, `src/main.ts`, `tsconfig.json`, `package.json`, and any local build helper. The trusted package manager creates package-lock.json; the coding agent must not fabricate it. Use plain TypeScript/HTML/CSS, exact development dependency `typescript: 5.9.3`, and no browser runtime dependencies. No messaging SDK, runtime CDN, external fonts/assets, service worker, or Python messaging source.

Supported build commands:

```sh
npm --prefix generated/typescript-web ci
npm --prefix generated/typescript-web run typecheck
npm --prefix generated/typescript-web run build
```

The manifest exposes typecheck (strict TypeScript checking without emit) and build (compile plus copy local HTML/CSS/assets). Build produces a self-contained `dist/index.html` and all its referenced local assets. TypeScript configuration targets ES2022 with DOM APIs and browser ES modules. Resolve module URLs correctly; no browser-side npm package resolution. Build may use a Node standard-library helper. Dist is disposable; only source and package-manager declarations/lock are committed.

The server serves dist and `/api/v1/*` at one loopback origin, default `http://127.0.0.1:8765`. API URLs are relative to that origin, never a hard-coded remote endpoint. The supported desktop test browser is the Chromium distributed with the retained Playwright version. Other browsers are unverified until tested. Different ports/hostnames/profiles are distinct stores; use the same origin/profile for persistence tests.

## User interface and observable selectors

The page has labeled controls and English status/error text. Support ordinary keyboard focus and submission, readable text, and visible errors. Insert message content as text, never executable HTML. Use pre-wrap or equivalent for exact whitespace/newline display. Show sender and text in inbox rows; recipient, text, state, and error in outbox rows. Include a brief note that server acceptance is not delivery/read confirmation.

| data-testid | Required element / state |
|---|---|
| app-ready | Root with data-ready=false until store opens and persisted state renders; true afterward. A failed startup remains false with visible error. |
| username-input | Username input shown before login; no trimming/case conversion. |
| login-button | Commits valid identity; invalid input leaves login available and shows error. |
| current-user | Displays the exact persisted username after login/restoration. |
| recipient-input | Address field, enabled after identity is ready and sync is not paused. |
| message-input | Multiline text field; preserve draft after invalid input/storage failure. |
| send-button | Enqueues through the real transaction; clear text only after successful commit. |
| inbox | Container ordered by recipient sequence. |
| outbox | Container ordered by local_order. |
| connection-status | Visible text and data-state=unknown/online/offline/error. |
| error-message | Visible local validation/storage/reset-required message; empty when none. |
| transport-mode | Select with values online/offline; labeled Development transport. Defaults online on each load. |
| reset-button | Opens a confirmation panel; does not itself clear data. |
| reset-confirm | Explicitly clears this application's store and returns to login. |

Inbox rows have data-testid=inbox-item, data-message-id, data-sender, data-sequence; children message-sender and message-text. Outbox rows have data-testid=outbox-item, data-message-id, data-state, data-local-order; children message-recipient, message-text, message-state, message-error. These repeated child IDs are scoped to their row. Machine-readable state is queued/accepted/failed; message-state text shows queued / accepted by server / failed. Empty lists show a helpful empty state without fake message rows.

Prevent duplicate submission while an enqueue transaction is pending; restore controls afterward. Do not truncate drafts to fit a character count: validate UTF-8 byte length and scalar validity explicitly. Network work must not block editing. A local form error remains until another form action resolves/replaces it; background polling must not immediately erase it. Outgoing transport/permanent errors remain visible per row. CURSOR_INVALID visibly asks for reset and disables new sends while leaving inspection and explicit reset usable.

## IndexedDB version 1

Database name: `reusable-spec-messenger`, version 1. One identity per browser origin/profile, one supported active tab for that identity. Tests use isolated browser contexts. Multiple tabs sharing a store are outside the supported-use precondition; document this rather than silently claiming coordination.

| Store | Key and values |
|---|---|
| metadata | keyPath `key`; singleton `{key:"state",username:null,receive_cursor:0,next_local_order:1}` initially |
| outbox | keyPath `message_id`; sender, recipient, text, local_order, state, server_sequence:null, error:null initially; unique index by_order on local_order |
| inbox | composite keyPath `[sender,message_id]`; recipient, text, sequence; unique index by_sequence on sequence |

Create all stores/indexes and initial metadata atomically in the version-change transaction. An existing unsupported database version/schema, blocked upgrade, denied access, quota error, or transaction abort must be visible without clearing the database. Close the connection on versionchange, stop synchronization, and ask the user to reopen. Baseline provides no migration to other versions.

Validate scalar input and enforce protocol limits before opening a write transaction. Enqueue uses one readwrite transaction over metadata/outbox: allocate safe integer order and a collision-free crypto.randomUUID(), insert immutable queued record, advance allocator. Reject enqueue with LOCAL_ORDER_EXHAUSTED when next_local_order is already 9007199254740991; the final allocatable order is 9007199254740990 so increment never overflows. Outcome uses an outbox transaction preserving payload. Receive uses one readwrite transaction over inbox/metadata, with conflict checks and atomic cursor advancement. UI success means transaction completion, not individual request success. Do not await fetch or unrelated asynchronous work inside a database transaction. Render snapshots after commit and keep identity/draft usable on recoverable failure.

## Network, lifecycle, and reset

Use fetch with AbortController, cache:no-store, redirect:error, and a five-second deadline covering receipt/body processing. Validate the exact protocol objects and cross-field consistency. A network TypeError/timeout is uncertain, never permanent rejection. Classify HTTP status even if its error body cannot be parsed. Use the single protocol scheduler: one POST head and one GET page per cycle, followed by a one-second delay. Wake at login/startup/reconnect and page activation; merge triggers and prohibit overlapping cycles. Background throttling is best effort; no closed-tab delivery.

Online/offline development control blocks requests through the same transport path while allowing offline enqueue. Browser online/offline events are hints, not proof of server reachability. Actual external outage tests must fail real API traffic. Reload persistence tests leave static assets accessible and keep the same origin/profile/server session.

Before confirmed reset, stop the scheduler, abort/invalidate in-flight requests using a generation token, and wait for existing transactions. Clear only this application's three stores and restore metadata defaults in a transaction. Ignore every response tied to the old identity/generation. Show login only when reset commits; a failed reset preserves the last committed store and shows an error. Do not clear unrelated origin storage or browser profiles. A canceled confirmation changes nothing. Reset restores online mode, unknown connection, and unpaused synchronization with no identity.

Implement connection/error observation semantics consistently with [the Python Status contract](PYTHON.md#machine-interface), without requiring the browser to expose a global mutation/debug API. Tests interact with the rendered controls and may inspect specified IndexedDB records read-only for cursors/atomicity. Failure injection belongs in retained fixtures, not fake acceptance paths inside the client.

## CHG-003 directory and receipt extension

Implement the explicitly registered [DIRECTORY.md](DIRECTORY.md) contract and its platform-specific selectors. It extends serialized scheduling and GUI observation, without changing version-1 durable storage, existing selectors, or the machine interface. Keep auxiliary errors separate from ordinary messaging errors and apply the same reset-generation guard to every response. Receipt progress comes only from committed inbox/cursor metadata; never infer it from display or a downloaded page.


## CHG-004 desktop-style layout

Make the web interface visually follow the Python desktop's task layout, using native HTML/CSS rather than copying Python code. Use compact neutral gray panels, dark readable text, thin borders and system fonts. No large marketing heading, excessive card padding, or oversized gaps. At a 1280×900 viewport after login all four work areas are visible without page scrolling: session controls at top, full-width compact known-recipient panel, full-width compose panel, then Inbox and Outgoing side by side. Their panel bottoms must fit within the viewport. Directory panel is at most 200px tall with a scrollable list. Use flexible heights and internal table scrolling rather than allowing message history to grow the page.

Expose panel selectors session-panel, directory-panel, compose-panel, message-panels, inbox-panel and outbox-panel. Session panel contains current-user, connection-status, Development transport, Reset and presence-status. Directory panel contains filter/Refresh, directory/receipt observations and the recipient list. Compose places labeled Recipient and Send on one row above a full-width multiline message input. A concise receipt explanation may sit between compose and history. Preserve all existing data-testid controls, row attributes and state/error semantics.

Use semantic tables: Inbox columns Message ID, Sender, Text, Sequence; Outgoing columns Message ID, Recipient, Text, State, Error, Order. Existing inbox/outbox selectors may identify table bodies; row and child selectors still expose exact complete strings for retained tests. Fixed-height scroll areas accommodate long lists and wide columns. Truncated visual previews must retain exact textContent; only CSS clips them. Selecting an inbox/outgoing row displays its full exact text in the respective readonly text element (inbox-detail/outbox-detail, such as pre; exact textContent, not a textarea value) below its table. Rows support click and Enter/Space keyboard selection, and selected rows are visibly highlighted. Details preserve Unicode, spaces and line breaks and are never rendered as HTML. Refresh must not clear current selection/details; reset must clear them.

At widths below 800px stack the two history panels and allow vertical page scrolling; controls remain usable at 390px width. Tables may scroll horizontally within their own panels but must not make the whole document wider than the viewport. No new runtime dependency, CDN, or storage change. Both platform schedulers implement the registered PRESENCE.md extension.
