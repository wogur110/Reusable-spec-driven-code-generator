# Python client contract

Status: current Python contract through CHG-004: Tkinter desktop, shared directory/durable receipts, and explicit presence. Normal launch opens the GUI; --machine remains display-free. Shared behavior is authoritative in [PRODUCT.md](PRODUCT.md), [PROTOCOL.md](PROTOCOL.md), [DIRECTORY.md](DIRECTORY.md), and [PRESENCE.md](PRESENCE.md). Historical verification is recorded in [STATUS](../docs/STATUS.md).

## Source and entry point

Generated boundary: `generated/python-client/`. Required entries: `main.py` and `gui.py`. Separate presentation, storage, validation/transport, and synchronization into local modules; other implementation filenames are free. Python 3.10+ standard library including tkinter/ttk with Tcl/Tk 8.6; no pip dependency, messaging SDK, browser implementation imports, or shared messaging source. Normal launch opens a desktop window. Real desktop widgets and the headless machine interface use the same production storage/synchronization core. Native Tk libraries are operating-system prerequisites listed in README/TESTING.

```sh
python3 generated/python-client/main.py --server http://127.0.0.1:8765 --state-dir var/alice
python3 generated/python-client/main.py --server http://127.0.0.1:8765 --state-dir var/test-alice --machine --transport offline
python3 generated/python-client/main.py --state-dir var/test-alice --reset-state --yes
```

Options: `--server` defaults to the origin above; `--state-dir` defaults to `var/python-client` relative to the current directory; `--machine` enables JSON-lines; `--transport online|offline` defaults online and is not persisted. `--help` exits 0 without opening a store or network connection. Validate server as an HTTP loopback origin, reject credentials/path/query/fragment, normalize hostname case and omit explicit port 80 for store comparison; retain other ports. Do not resolve arbitrary public hostnames as a way to accept an origin: allow localhost or literal loopback addresses only.

`--reset-state` requires `--yes` and a stopped client. Delete only `messages.sqlite3` and its recognized `-journal`, `-wal`, `-shm` companions from the selected state directory, preserving unrelated files. Reset exits without logging in or starting synchronization. Missing confirmation fails; never silently destroy a store due to startup or protocol errors. Do not create a store merely to reset an absent one.

## SQLite version 1

Store at `<state-dir>/messages.sqlite3`. Use `PRAGMA user_version=1`, foreign keys enabled, `synchronous=FULL`, explicit transactions, and one application storage lock. Default rollback journaling is sufficient. New database creation and metadata initialization are atomic. An existing version other than 1 fails as STORE_VERSION_UNSUPPORTED without modifying it; baseline has no migration. Existing version 0 with application tables is not silently reinitialized. Reject an incompatible schema visibly. Best-effort prevention of a second process may use a documented OS lock; concurrent instances using one store are unsupported and must not be used by tests.

| Table | Required schema |
|---|---|
| metadata | Singleton `id=1`; nullable TEXT username, TEXT server_origin, INTEGER receive_cursor default 0, INTEGER next_local_order default 1. |
| outbox | TEXT message_id primary key; TEXT sender/recipient/text not null; INTEGER local_order unique; TEXT state constrained to queued/accepted/failed; nullable INTEGER server_sequence; nullable TEXT error_code/error_message. |
| inbox | TEXT sender/message_id composite primary key; TEXT recipient/text not null; INTEGER sequence unique. |

Persist server_origin on creation and compare it at startup; mismatch fails as STORE_ORIGIN_MISMATCH and asks for an explicitly chosen fresh store. Preserve one identity. A valid same-name login is idempotent; a different name returns IDENTITY_LOCKED. Validate strings before SQLite encoding. Allocator values stay within the protocol's safe-integer range. Reject enqueue with LOCAL_ORDER_EXHAUSTED when next_local_order is already 9007199254740991; the final allocatable order is 9007199254740990 so increment never overflows.

Enqueue transaction: validate, allocate a collision-free UUIDv4 and local order, insert queued record with null sequence/error, increment allocator, commit; return a result only after commit. Local validation/storage failure must not dispatch network activity for that message. Outcome transaction: set accepted plus sequence or failed plus reason; never change payload fields. Receive transaction: validate complete page, insert/compare inbox rows, advance cursor, commit atomically. Snapshots read metadata and records consistently under the lock. Reject conflicting duplicate inbox rows rather than overwriting them.

If an outcome write fails, leave the previously committed row queued and report the error so idempotent retry remains possible. If a receive write fails, preserve both old inbox and old cursor. Startup failures exit visibly; recoverable operation failures keep the process usable.

## Concurrency and transport

One background worker implements the serialized messaging/directory/receipt/presence scheduler; the Tk main thread remains responsive. Only the main thread touches widgets; marshal committed snapshots through after/queues. Hold the storage lock only for short transactions/snapshots, never network calls or input. Serialize stdout writes. Message requests have a five-second total HTTP deadline including body reads; directory/receipt/presence requests have two seconds. Follow PROTOCOL/DIRECTORY/PRESENCE for ordering and exact validation. Use no redirects or environment proxy routing. The development toggle controls real transport and schedules the bounded presence transition; it never pretends acceptance or inserts messages directly.

On window close or SIGINT (and on quit/stdin EOF in machine mode only): stop scheduling, finish or cancel the current bounded request, do not start a new receive afterward, complete owned storage work, close the database, and exit within six seconds. Exit 0 for ordinary shutdown and help, 2 for unusable startup/reset arguments or store. Runtime command errors keep the client running. Human display updates must not destroy a partially typed draft.

## Desktop interface

Use Tkinter/ttk, window title `Local Messenger - Python`, English labels, and a resizable window initially at least 960 by 640 pixels. Match the browser's task sequence: identity and connection header, recipient and multiline text composer, Send, Development transport, Reset local store, and side-by-side Inbox/Outgoing panels. Include a visible note that accepted by server is not a delivery/read receipt. Comparable grouping and wording matter; platform styling may differ. Scrollbars and message-detail panes must allow reading complete long/multiline messages without logs. Keep editing focus/draft/selection through background refreshes. Enter in the multiline composer inserts a newline; sending uses the Send button. Ordinary keyboard traversal works.

Before login show username and Log in; preserve invalid input and show the error. Restore saved identity without prompting. Disable composition until identity is ready, and while CURSOR_INVALID pauses synchronization. Show errors visibly, including storage/startup/reset errors. A local form error persists until the next form action resolves/replaces it. Show per-message errors for failed or retrying sends. Clear the composer only after a successful durable enqueue. Never trim text, silently truncate it, or replace its original code points.

Development transport is a readonly online/offline selection, default online on launch. It controls the production transport abstraction. Reset local store opens an explicit confirmation with Confirm reset and Cancel. Cancel preserves everything. Confirm stops scheduling and invalidates/finishes in-flight operations before clearing only the selected application's SQLite data and restoring version-1 metadata. Preserve unrelated files. Return to login with online/unknown/unpaused state only after successful reset; old responses must never populate a new identity's store. Keep reset and inspection usable during CURSOR_INVALID. Preserve the existing SQLite version-1 schema: a pre-GUI store opens without migration or loss of identity, IDs, order, state, messages, and cursor.

Closing the window gracefully stops the worker and exits within six seconds even during a request; do not start another request after closing. Default GUI launch does not read stdin or exit when stdin is closed. --machine, --help and the stopped --reset-state operation work without Tk or a display; import Tk lazily. Missing GUI prerequisites produce an actionable stderr error and exit 2, without clearing a store.

### Retained GUI automation contract

`gui.py` exports `DesktopApp(root, server_origin, state_dir, transport="online")`, where root is an existing tkinter.Tk and state_dir accepts a path string. Production main.py creates this same class and runs root.mainloop(). The constructor creates the widgets below immediately; successful startup sets `app.ready=True` only after durable state has rendered. An unusable store leaves ready false with a visible error and a closable window. `app.close()` is the same callback registered for WM_DELETE_WINDOW, including graceful worker/storage shutdown and root destruction. No parallel test messaging implementation is permitted.

Expose `app.widgets`, a mapping to the actual production Tk widgets, for retained tests to enter text, invoke buttons, generate selection events, and read displayed state. This is an observation/control locator contract, not a backend mutation API.

| Key | Tk widget and observable contract |
|---|---|
| username-input | Entry/ttk.Entry before login; exact text input |
| login-button | Button/ttk.Button invoking normal login |
| current-user | Label/ttk.Label whose text is the exact saved username, or empty before login |
| recipient-input | Entry/ttk.Entry |
| message-input | tkinter.Text; get("1.0", "end-1c") is the exact draft |
| send-button | Button/ttk.Button using the normal enqueue handler |
| connection-status | Label/ttk.Label text exactly unknown/online/offline/error; put descriptive prefixes in a separate label |
| presence-status | Label/ttk.Label text exactly unknown/pending/confirmed/error for the current mode notification; follow PRESENCE.md and keep it separate from connection/delivery state |
| error-message | Label/ttk.Label text empty or a visible actionable error |
| transport-mode | ttk.Combobox values online/offline; <<ComboboxSelected>> runs the production handler |
| reset-button | Button/ttk.Button showing confirmation |
| reset-confirm / reset-cancel | Button/ttk.Button visible only during confirmation; normal reset/cancel handlers |
| inbox | ttk.Treeview; iid is sender + ":" + message_id; values in order sender, text, sequence; rows in sequence order |
| outbox | ttk.Treeview; iid is message_id; values in order recipient, text, state, error, local_order; rows in local order; state text queued / accepted by server / failed |
| inbox-detail / outbox-detail | Readonly tkinter.Text; selecting a row via <<TreeviewSelect>> shows its exact message text, excluding Tk's terminal newline |

Tree column #0 displays the message ID for inspection. Text/values are data, never Tcl code. Detail panes preserve spaces and newlines. Do not promise glyphs for nonprinting scalar values; persisted and machine values remain exact. Retained tests query real widgets, may inspect SQLite read-only for cursor/schema assertions, and inject real transport faults outside the application. They must not call messaging methods to bypass GUI handlers. The JSON-lines machine interface below remains available for deep protocol/scalar boundaries and does not require a display.

## Machine interface

Use UTF-8 JSON, one object per line, flushed stdout. Logs go to stderr; no prompts/ANSI output on stdout. Cap each input line at 65,536 bytes; consume the remainder of an oversized line and return INVALID_COMMAND. Duplicate JSON members, invalid UTF-8/JSON, nonfinite tokens, unknown commands/members, or wrong parameter types return INVALID_COMMAND. Validate username/text semantics through the same production operations.

Every command has exactly `id`, `command`, and its listed parameters. ID is a nonempty ASCII string of at most 64 characters; echo it exactly. Invalid/missing ID produces id:null in the error result. Correlation IDs are not messaging idempotency keys; every valid send command is a new submission, even with a reused correlation ID. Emit exactly one result per input line.

| Command | Parameters | Successful data |
|---|---|---|
| login | username string | `{username}` after commit |
| send | recipient string, text string | `{message_id,state:"queued",local_order}` after commit |
| inbox | none | `{messages:[Message,...]}` sorted by sequence |
| outbox | none | `{messages:[Outgoing,...]}` sorted by local_order |
| status | none | Status below |
| transport | mode string online/offline | Status after mode change |
| quit | none | `{}` followed by shutdown |

Outgoing has exactly `message_id`, `sender`, `recipient`, `text`, `local_order`, `state`, `server_sequence` (integer/null), `error` (null or `{code,message}`). Machine state is `accepted`; human wording is “accepted by server.” Status has exactly `username` (string/null), `transport` (online/offline), `connection` (unknown/online/offline/error), `cursor`, `pending_count`, `sync_paused` (boolean), `last_error` (null or `{code,message}`). Pending means queued only.

Startup connection is unknown (offline in explicit offline mode); valid requests establish online, transport failure offline, protocol/storage errors error. An entire successful cycle clears the previous synchronization last_error; a successful receive alone does not hide a send error. CURSOR_INVALID pause takes priority. Connection/last_error/pause are process-local observations; outbox errors persist. Store-level failures cannot be hidden by an apparent healthy connection.

```jsonl
{"id":"login-1","command":"login","username":"alice"}
{"type":"result","id":"login-1","ok":true,"data":{"username":"alice"}}
{"id":"send-1","command":"send","recipient":"bob","text":"Hello Bob"}
{"type":"result","id":"send-1","ok":true,"data":{"message_id":"11111111-1111-4111-8111-111111111111","state":"queued","local_order":1}}
```

An error result is `{"type":"result","id":"send-1","ok":false,"error":{"code":"SELF_SEND","message":"Choose a different recipient."}}`. Error prose is explanatory, not asserted verbatim. Local codes add INVALID_COMMAND, IDENTITY_REQUIRED, IDENTITY_LOCKED, STORAGE_UNAVAILABLE, STORE_VERSION_UNSUPPORTED, STORE_ORIGIN_MISMATCH, STORE_IN_USE, LOCAL_ORDER_EXHAUSTED, TRANSPORT_ERROR, PROTOCOL_ERROR, and HTTP_ERROR to the protocol codes. Enqueue is rejected while synchronization is paused with CURSOR_INVALID; idempotent same-name login, snapshots, transport inspection, and quit remain usable.

Emit ready exactly once after successful initialization: `{"type":"event","event":"ready","username":null,"transport":"online","cursor":0}` (use actual restored values). After committed identity/outbox/inbox changes, emit `{"type":"event","event":"state_changed","revision":1}` with a process-local increasing revision; coalescing changes is allowed. Events may interleave with results; send success still implies committed enqueue. Emit `{"type":"event","event":"shutdown"}` before ordinary exit, after storage closes. Tests observe snapshots rather than depend on exact event counts. No separate test-only messaging implementation or mutation API is allowed.

Verification coverage is defined in [ACCEPTANCE.md](ACCEPTANCE.md), including both human usability and machine-driven behavior.

## CHG-003 directory and receipt extension

Implement the explicitly registered [DIRECTORY.md](DIRECTORY.md) contract and its platform-specific selectors. It extends serialized scheduling and GUI observation, without changing version-1 durable storage, existing selectors, or the machine interface. Keep auxiliary errors separate from ordinary messaging errors and apply the same reset-generation guard to every response. Receipt progress comes only from committed inbox/cursor metadata; never infer it from display or a downloaded page.


## CHG-004 explicit presence override

The registered [PRESENCE.md](PRESENCE.md) extension adds explicit mode notifications and overrides heartbeat-only presence and the blanket offline-request prohibition within its defined bounds. Preserve all other contracts.

Reset readiness includes hidden widgets: inbox, outbox and user-directory Treeviews must contain zero items before username-input becomes mapped/enabled, even if their parent frames are hidden. Clear their selection/detail state and cached snapshots too. Hiding the old frame is not clearing old rows. Apply the cleared snapshot and login readiness together on the Tk thread; an old snapshot must never repopulate those widgets afterward. This makes the existing reset contract observable consistently through actual widget state.
