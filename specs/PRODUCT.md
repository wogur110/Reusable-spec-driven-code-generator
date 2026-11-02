# Product specification

Status: current product contract includes CHG-001 client desktop, CHG-002 retained server desktop, CHG-003 directory/receipts, and CHG-004 desktop-style web layout and explicit client presence. See STATUS for executed acceptance, regeneration, and pending manual evidence. Read [the decision record](../docs/DECISIONS.md) for effective choices and provenance.

## Your product choices

Edit only `Your input` to change a preference. Adjacent defaults describe the finished CHG-001–004 baseline. Blank, whitespace-only, `TBD`, and `—` use those defaults; unchanged blanks preserve completed features. `false`, `0`, and `none` are explicit values subject to compatibility review. Every regeneration request includes checking changed choices and reconciling affected contracts before generation; see [the default workflow](../README.md#default-regeneration-instruction). Technical requirements below are agent-maintained derived content.

<!-- USER:BEGIN PRODUCT_CHOICES -->
| ID | Question | Your input | Example / automatic default |
|---|---|---|---|
| P01 | What is the project called? | | `reusable-spec-driven-code-generator` |
| P02 | What should the project demonstrate? | | A reusable generator can recreate independent Python and TypeScript messaging clients from a precise specification. |
| P03 | Who will use or review it? | | A developer or reviewer running a small local demonstration on one computer. |
| P04 | What interfaces should the two clients have? | | Python Tkinter desktop GUI and TypeScript browser client with a comparable compact desktop layout; retain the Python headless machine interface. |
| P05 | What should the browser screen contain? | | Session/transport/reset controls, presence report, filterable known recipients with Refresh, recipient and multiline composer with Send, and side-by-side Inbox/Outgoing tables with exact text details; stack history on narrow screens. |
| P06 | How should identity work? | | Enter a username on first launch and remember it across normal restarts; use an explicit reset to change identity. No password. |
| P07 | What must survive a client restart? | | Username, queued messages with their original IDs, received messages, and synchronization progress. |
| P08 | Which offline experience is required? | | A running desktop client or loaded page queues locally during an outage. Selecting Offline permits one bounded presence notification, then stops API traffic; reconnect resumes synchronization. Offline browser asset load/reload is excluded. |
| P09 | What send feedback should users see? | | `queued`, `accepted by server`, or `failed`, with an actionable error; server acceptance is not a read/delivery receipt. |
| P10 | What additional feature is essential? | | Server Start/Stop/monitoring GUI; shared recipient directory and click-to-address; durable receive acknowledgments and per-user Sent/Received/Queued views; explicit Online/Offline presence with heartbeat fallback. Offline client queues remain unknown to the server. |
| P11 | What is intentionally out of scope? | | Attachments, groups, reactions, passwords, cloud deployment, push notifications, closed-app delivery, and read receipts. |
<!-- USER:END PRODUCT_CHOICES -->

## Scope and operating assumptions

The deliverable is a configurable generation harness; local messaging demonstrates its behavior. The independent Tkinter desktop and plain TypeScript/HTML/CSS browser clients implement [PROTOCOL.md](PROTOCOL.md) with the registered [DIRECTORY.md](DIRECTORY.md) and [PRESENCE.md](PRESENCE.md) extensions. The retained server provides terminal and desktop operation. Completed requests supply the current defaults above; previous values and provenance are recorded in [DECISIONS.md](../docs/DECISIONS.md). All user-authored input cells remain unchanged.

Regeneration uses this current contract and reconciles changed USER preferences before freezing inputs. With no changed choices, preserve the completed baseline. Pending FUTURE.md requests become requirements only after a separate apply request. Only the two client directories are generated outputs; server, tests, scripts and harness remain retained inputs.

One running server instance defines a demonstration session; a GUI Stop followed by Start begins a new session in the same process. One running client instance per username and one browser tab per identity are supported. Different clients use different identities and stores. There is no registration service, authentication, authorization, production hosting, or protection against impersonation. Client persistence assumes a writable store that the user/browser has not deleted or evicted. Network requests cannot guarantee exactly-once transmission.

## Resolved requirements

| ID | Required behavior | Source |
|---|---|---|
| REQ-GEN-01 | Generate working clients through an actual Codex invocation; source must not be restored from a prior implementation. Shared and platform-specific inputs are declared in configuration. | Source requirements; W01 |
| REQ-GEN-02 | Recreate both clients from retained inputs in a fresh workspace with no old client source or Git objects, and pass the same frozen acceptance tests. | Source requirements; P02 |
| REQ-GEN-03 | Permit explicitly registered specification extensions and selected targets without application-specific branches in generic orchestration. DIRECTORY.md and PRESENCE.md are active for both clients; recorded CHG-001–004 evolution evidence remains separate from future unexecuted changes. | Source requirements; guide Section 5; CHG-001–004 |
| REQ-LOCAL-01 | Application runtime and assets are local. Use a small in-memory Python server and no turnkey messaging SDK, external runtime service, or runtime CDN. | Source requirements; D02–D03 |
| REQ-ID-01 | Prompt for a username on first launch, persist it before use, restore on restart, and require explicit reset to change identity. Exact ASCII `[a-z][a-z0-9_]{0,31}`; no trimming or case conversion. | P06; derived validation |
| REQ-SEND-01 | Address a message to any valid different username, including a recipient who has never launched. No recipient registration check. | Source requirements; derived addressing |
| REQ-TEXT-01 | Accept 1–4,096 UTF-8 bytes of Unicode scalar text; preserve whitespace, newlines, and code points exactly. Whitespace-only text is valid. Reject lone surrogates, empty strings, and oversized text locally and on the server. | A03; derived limit |
| REQ-QUEUE-01 | Commit a new UUIDv4, immutable sender/recipient/text payload, and local FIFO order as queued before any send attempt. A failed enqueue produces no network send. | P07–P08 |
| REQ-STATE-01 | Persist queued, accepted, or failed state; present accepted as “accepted by server.” Accepted is not proof that a recipient received/read a message. Preserve failed rows and actionable reasons. | P09 |
| REQ-SYNC-01 | Use one serialized scheduler: prioritize pending presence intent, then one queued send and one incoming page, followed by durable receipt, heartbeat and directory work. Receive still runs after send failure. Message deadlines are five seconds; auxiliary/presence deadlines are two seconds; wait one second between finished cycles. Follow DIRECTORY.md and PRESENCE.md for transition priority and failure isolation. | Source requirements; derived scheduling; CHG-003–004 |
| REQ-RETRY-01 | Retry uncertain/temporary outcomes with the same ID and payload; permanent rejection fails that entry and permits later queued entries to proceed. No automatic payload editing or ID replacement after transmission. | A02; P07 |
| REQ-ORDER-01 | Send queued entries in ascending local order. Display incoming entries by the recipient's server sequence. Different recipients have independent sequences; no global ordering promise. | Derived ordering |
| REQ-DEDUPE-01 | Within one server session, exact retries return the original receipt without creating another message. Persistently prevent duplicate inbox rows by sender and message ID. | A02 |
| REQ-RECEIVE-01 | Fetch contiguous recipient pages and commit inbox rows and cursor atomically. Validate an entire page before committing. Failure never skips uncommitted messages. | P07; derived durability |
| REQ-PERSIST-01 | Normal client restart retains identity, original pending IDs/payloads/order, accepted/failed outbox rows, inbox, and cursor. Unsupported store versions fail visibly without clearing data. | P07; A01 |
| REQ-FAILURE-01 | Invalid commands/drafts do not enqueue. Storage failures remain visible; acceptance-write failure leaves the original queued entry available for retry. Invalid receive pages leave storage unchanged. | A03; derived failure behavior |
| REQ-SESSION-01 | The server retains accepted messages for one running server instance (one Start/Stop session in the server GUI). After restarting it, explicitly reset demo client stores; automatic cross-session reconciliation is excluded. CURSOR_INVALID pauses synchronization until reset. | D04 |
| REQ-UI-01 | Both clients show incoming sender/exact text and outgoing recipient/text/state/error. Automatic synchronization must not block input. Both provide graphical login, compose, inbox/outgoing, transport, and confirmed-reset controls; Python uses PYTHON.md and browser uses TYPESCRIPT.md. | P04–P05; A04 |
| REQ-TEST-01 | Test actual clients, desktop and browser interactions, independent transport faults, reversed roles, and the fixed scenario. Observable transitions have 30-second deadlines; required tests cannot be skipped or weakened during repair. | Source requirements; A01–A05; W04 |
| REQ-RELEASE-01 | Record authorship separately from generated/retained ownership. Preserve real incremental commits, committed client source/locks, verification evidence, and an archive with restorable Git history. | Source requirements |

## Observable limits

The receive guarantee is one visible inbox row per `(sender,message_id)` under a continuing server session and intact local store, despite retries and normal restarts. It does not promise exactly-once network delivery, server crash recovery, or delivery after local state is lost. Messages accepted by the server remain available when their recipient is offline.

An already-loaded browser page can queue during an API outage; first load or reload requires its local assets to be reachable. Closed-tab/closed-process delivery and reliable background-tab timing are excluded. Reopening or activating a client resumes synchronization. Unknown wire fields are rejected until an extension is explicitly registered and reconciled. No message labels, message-content search, attachments, or group feature is selected; CHG-003 adds only local username filtering.

Platform contracts: [PYTHON.md](PYTHON.md), [TYPESCRIPT.md](TYPESCRIPT.md). Requirement coverage: [ACCEPTANCE.md](ACCEPTANCE.md).

## CHG-002 server operation

REQ-SERVER-UI-01: Provide an optional local Tkinter/ttk server control window for starting, stopping, and monitoring the same retained HTTP server. Follow [SERVER.md](SERVER.md) for lifecycle, controls, monitoring, and error behavior. The terminal server, wire protocol, independent clients, and client stores remain compatible. Each new server instance starts empty, even within one GUI process. Source: explicit CHG-002; no USER preference cell changes.

## CHG-003 directory and activity requirements

REQ-DIR-01: All three GUIs show the shared session directory, allow local username filtering and refresh, and distinguish advisory presence from reachability. The server displays Online/Offline; client lists display recently seen/not recently seen. Both clients allow click-to-address without automatic send, preserving manual addressing and drafts.

REQ-RECEIPT-01: Clients report only durably committed receive progress through idempotent cumulative acknowledgments. GET, server acceptance, online status and operator inspection are not receipt/read confirmation.

REQ-ACTIVITY-01: Server selection exposes that user’s accepted Sent, acknowledged Received, and inbound Queued messages with exact details. The user explicitly chose queued=server-accepted awaiting recipient acknowledgment; offline client queues are unknown. No outbox telemetry or account/message administration.

These requirements are defined by the registered [DIRECTORY.md](DIRECTORY.md) extension. P10's input cell stays blank; its adjacent default now reflects the completed explicit requests. Both earlier GUI requests remain implemented. Existing client version-1 data and messaging behavior must survive regeneration without migration.


## CHG-004 presence and web layout requirements

REQ-PRESENCE-01: Client mode changes explicitly update server presence independently of other-user traffic. Offline permits one final two-second notification after existing work, then no API traffic; healthy server display updates within eight seconds. Only explicit Online clears the offline latch; a 15-second heartbeat timeout handles uncommunicated disconnections. Follow [PRESENCE.md](PRESENCE.md), including notification failure and reset guards.

REQ-WEB-UI-02: Compact desktop-style browser workflow with session, directory, compose, and side-by-side history/detail panels at 1280×900; stack history below 800px and remain usable at 390px. Preserve exact text, selection, keyboard controls, and [TYPESCRIPT.md](TYPESCRIPT.md) selectors. Version-1 stores and message acceptance semantics remain unchanged.
