# Python client contract

Status: Stage 1 specification; commands below are PLANNED — not implemented or verified. Shared behavior is authoritative in [PRODUCT.md](PRODUCT.md) and [PROTOCOL.md](PROTOCOL.md).

## Source and entry point

Generated boundary: `generated/python-client/`. Required entry: `main.py`. Separate presentation, storage, validation/transport, and synchronization concerns into local modules; implementation file names other than main.py are free. Python 3.10+ standard library only; no pip dependency, messaging SDK, browser implementation imports, or shared messaging source. Tests drive the same application operations as the human interface.

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

One background worker implements the protocol's serialized cycles; the main thread remains responsive to commands. Use the storage lock for short transactions/snapshots only, never across network calls or user input. Serialize writes to stdout. Use a five-second total HTTP deadline including body reads, no redirects, and no environment proxy routing. Validate status/content type/body independently as specified in PROTOCOL.md. A development transport toggle uses the real transport abstraction; it does not pretend acceptance or insert messages directly.

On quit, stdin EOF, or SIGINT: stop scheduling, finish or cancel the current bounded request, do not start a new receive afterward, complete owned storage work, close the database, and exit within six seconds. Exit 0 for ordinary shutdown and help, 2 for unusable startup/reset arguments or store. Runtime command errors keep the client running. Human display updates must not destroy a partially typed draft.

## Human interface

If identity is absent, prompt exactly `Username:`; invalid input shows a reason and prompts again without trimming. A restored identity skips this prompt. Show the current username, server origin, and command hint. On incoming commits, print sender and exact text; on outgoing changes, show message ID and queued / accepted by server / failed plus error. Render text unambiguously, preserving newlines and spaces in lists.

| Command | Behavior |
|---|---|
| `send bob Hello Bob` | Recipient is the token after send; text is the exact remainder after its single separator, preserving additional spaces. |
| `send-json bob "First line\nSecond line"` | Decode exactly one JSON string and use normal text validation; useful for embedded newlines. |
| `inbox` | Show persisted incoming rows in sequence order. |
| `outbox` | Show persisted outgoing rows in local_order, including exact text, recipient, ID, state, and error. |
| `status` | Show identity, mode, observed connection, cursor, pending count, pause, and last error. |
| `transport offline` / `transport online` | Change the real transport mode; online schedules immediate synchronization unless paused. |
| `help` / `quit` | Explain commands / shut down cleanly. |

Typing a new username after login is not an identity-switch command. `send` need not echo the full text in its immediate acknowledgment; `outbox` is the authoritative inspection command.

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
