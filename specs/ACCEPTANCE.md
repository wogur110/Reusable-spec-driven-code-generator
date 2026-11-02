# Acceptance contract

Status: the unchanged CHG-004 runtime contract passed 92 acceptance cases after P01 reconciliation and all-client regeneration, with nine harness guards passing. Clean proof `20261102T010021541172Z` passed all 92 cases inside the harness and standalone. [STATUS](../docs/STATUS.md) and [EVIDENCE.json](../docs/EVIDENCE.json) preserve actual results and failed attempts. P01 changes project documentation identity only; generated clients may not edit retained tests.

## Your acceptance expectations

Blank preferences use adjacent defaults, which include the completed baseline. Examples express expectations, not observations. A regeneration request includes reconciling changed choices before freezing specifications/tests; see [the default workflow](../README.md#default-regeneration-instruction). Actual manual results belong in [TESTING.md](../TESTING.md#your-manual-observations).

<!-- USER:BEGIN ACCEPTANCE_CHOICES -->
| ID | Question | Your input | Example / automatic default |
|---|---|---|---|
| A01 | Which restart scenario matters most? | | Given a queued message, when I restart that client with the same store and reconnect, its original text is delivered once. Browser assets remain reachable during reload. |
| A02 | What repeated-send failure should be checked? | | Given the server accepts a message but its reply is lost, when the client retries, the recipient still sees one inbox entry. |
| A03 | What should happen to invalid input? | | Empty messages and invalid recipients show a clear error; valid Unicode, spaces, and newlines are preserved exactly. |
| A04 | What manual usability check matters? | | I can distinguish queued from accepted messages and find the sender and exact text of each incoming message without reading logs. |
| A05 | What extra acceptance case do you want? | | Preserve the fixed scenario, A01–A04, derived boundary tests, and completed GUI/server/directory/receipt/presence/web-layout cases; no pending FUTURE feature is selected. |
<!-- USER:END ACCEPTANCE_CHOICES -->

## Project-name reconciliation scope

P01 names the project Jaehyeok-spec-driven-code-generator in documentation. Existing GUI titles/selectors, storage/package identifiers and behavior remain unchanged. Retained application assertions required no change; P01 input/default/title/provenance consistency was checked separately. Requested all-client generation, published acceptance and independent clean proof passed the full existing contract.

## Fixtures and observation rules

Use a real server on an allocated loopback port, a real Python subprocess, and Chromium with real page interactions. Each case owns isolated stores and processes. Per-client retained HTTP proxies independently inject API faults while forwarding static assets; the server remains alive. Browser-wide offline is a separate case after page load. Tests must not manipulate production queues to pretend a send or receive occurred. Direct API seeding is allowed for server fixtures and pagination; state-file setup is allowed only for explicit storage/version cases.

Python protocol boundaries use [its machine interface](PYTHON.md#machine-interface); CHG-001 graphical scenarios use the real widgets in [the desktop contract](PYTHON.md#retained-gui-automation-contract), and browser controls through [its selectors](TYPESCRIPT.md#user-interface-and-observable-selectors). Capture transport attempts and persisted snapshots so retries can be checked for unchanged IDs/payloads. Observe inbox contents, not just a successful HTTP call. Poll conditions with a monotonic 30-second deadline for each required transition. An observation cadence is not evidence by itself. A deadline failure is FAIL, not a reason to increase timing silently or skip the case. Build/tool timeouts are separate in [GENERATE.md](../GENERATE.md).

Required text fixtures: greeting `Hi Bob, I have something important to tell you`; reply `What is it?`; Alice queued text `Alice queued while offline`; Bob queued text `Bob queued while offline`. Exact Unicode fixture: `  한글 😀\nsecond line  `, where `\n` denotes a literal LF after the emoji. The reverse-direction Unicode fixture replaces 한글 with 답장. Use unique valid UUIDs for direct API seeds and retain client-issued IDs for assertions.

## Fixed offline scenario

Run once with Python=alice/browser=bob and again with browser=alice/Python=bob. Use independent external API proxies for this scenario; client development toggles are tested separately.

| Step | Action and completion criterion |
|---|---|
| 1 | Alice submits the exact greeting. Await Alice accepted and one matching Bob inbox row. |
| 2 | Bob submits the exact reply. Await Bob accepted and one matching Alice inbox row. |
| 3 | Block Alice's API transport. Alice submits her queued fixture; await an actual failed attempt and verify the row remains queued with its original ID. |
| 4 | Block Bob's API transport. Bob submits his queued fixture; verify queued and no new server acceptance for that ID. |
| 5 | Restore only Alice's API. Await her queued row accepted and confirm Bob's remains queued. |
| 6 | Block Alice again after acceptance. Keep server and Bob's store alive. |
| 7 | Restore Bob's API. Await his queued row accepted and Alice's queued text in his inbox; their relative observation order is not asserted. |
| 8 | Restore Alice. Await Bob's queued text in her inbox. Each final inbox has exactly its two expected entries in order, each ID once; each outbox has two accepted entries. |

## Required automated cases

Rows may expand into several executable tests. Reports must map collected tests to these IDs and contain nonzero counts, no required skips, no unexpected failures, and no flaky passes. Automatic assertion retries are limited to bounded observations; no whole-test rerun converts a failure into a clean first-pass result.

| ID | Stimulus | Required observations |
|---|---|---|
| AT-01 | First launch, invalid names, valid login, same-name login, attempted identity change, ordinary restart; confirmed/canceled browser reset and stopped Python reset; desktop confirmed/canceled reset | Names persist; invalid inputs do not establish identity; another name is rejected until reset; confirmation is necessary; unrelated store files/storage survive reset. |
| AT-02 | Send greeting/reply and exact Unicode/space/newline fixtures in both directions | Sender accepted; receiver shows exact sender/text once, in sequence order. |
| AT-03 | Fixed scenario with Python Alice | All eight steps and final counts above pass under independent API faults. |
| AT-04 | Fixed scenario with browser Alice | Same results with roles reversed. |
| AT-05 | Send to valid carol before she launches; test both recipient implementations | Acceptance precedes recipient login; logging in later receives the retained message. No registration dependency. |
| AT-06 | Queue three entries offline for one recipient; restore transport; then inject 500 for the queued head while an incoming message is available | Sends reach server in local order; only queued head retries; a failed send does not block receiving; recovery delivers all entries once and in order. Test both senders. |
| AT-07 | Proxy forwards a POST, receives successful acceptance, then drops its response before the client sees it | Client retries identical ID/payload; server responds 200 on replay; recipient and server each contain one message. Test both senders. |
| AT-08 | Direct exact replay, changed text, changed valid recipient, same ID under another sender, and concurrent exact requests | 201 first, 200 exact original receipt, 409 conflicts with no allocation; another sender independent; concurrent exact requests allocate one sequence only. |
| AT-09 | Queue behind blocked API; restart Python / reload page with assets available and same store/origin; recover; then restart after receiving | Identity, pending ID/text/order/state survive; eventual one delivery; inbox and cursor persist and do not duplicate. Test both platforms. |
| AT-10 | Seed 205 incoming messages while recipient inactive, then start it; separately seed 100 texts each containing 4,096 NUL scalar characters | All 205 exact ordered entries, cursor 205; page boundaries 100/200/205, each page at most 100. The maximum-size escaped page also arrives intact with cursor 100. Repeat both checks for both recipients. |
| AT-11 | Empty text, invalid recipient, self-send, 4,097 ASCII bytes, 1,025 emoji, lone surrogate where interface permits; valid whitespace, 4,096 ASCII bytes, 1,024 emoji | Invalid submissions show error, preserve graphical drafts, create no durable row/network POST. Valid boundaries preserve text and enqueue. API enforces the same limits. Test representable UI values and machine/wire scalar boundaries. |
| AT-12 | Actual browser network offline after loading; also exercise both development transport controls | Already-loaded page can enqueue; request genuinely fails and entry stays queued; restore transport and observe one delivery. Mode controls do not bypass production storage/transport logic. |
| AT-13 | Per client: POST timeout, 408, 429, 500, redirect, malformed/mismatched 201 receipt, permanent 400/409; GET wrong recipient/gapped sequence/bad next_after; valid CURSOR_INVALID | Uncertain sends keep IDs queued; permanent sends fail and later entries proceed; malformed pages preserve complete inbox/cursor; later valid page recovers; cursor error pauses both directions and demands reset. |
| AT-14 | Wire framing/schema errors, duplicate JSON request members, unknown fields/routes, media/body limits, bad/repeated query keys, invalid cursors; static resources and health | Exact status/code/field mapping; no acceptance from invalid sends; browser assets and requests stay local; no store/session claim from health alone. |
| AT-15 | Fresh retained-input workspace, actual harness all-target generation, build, and the complete current acceptance suite: AT-01–AT-14, AT-16–AT-17, GUI-01–06, SG-01–06, DIR-01–08, PRES-01–05 and WEB-01 | No previous clients/Git/transcripts supplied; all frozen checks pass inside the harness and standalone, retained inputs unchanged; original working tree preserved. This outer proof is excluded from ordinary verification to prevent recursion. |
| AT-16 | Client starts with unsupported store version or incompatible stored origin (Python); input during a delayed network request; normal quit with a request in flight | Startup error visible without destructive reset; local interaction remains responsive; quit completes within six seconds; no new work after shutdown. |
| AT-17 | Deliver invalid multi-row page containing one valid-looking row and one bad row; then recover with a valid page | Neither first row nor cursor commits from the bad page; recovery inserts the complete valid page atomically. Repeated/stale pages do not create duplicate rows. Test both platforms. |
| AT-18 | Harness config/path/integrity and publication failures using controlled runner fixtures | Reject output escapes/symlinks, changed retained files, missing outputs, incomplete agent events, zero-test results, and timeouts. Preserve existing published clients and rollback a partial publication. Unit checks do not replace AT-15's real generation proof. |

Current full verification collects AT-01–AT-14, AT-16–AT-17 and all completed-change cases below: GUI-01–06, SG-01–06, DIR-01–08, PRES-01–05 and WEB-01. Harness verification covers AT-18 separately. Implementation verification also requires AT-15 and documentation/build checks. These acceptance IDs expand to 92 executable cases in the last verified snapshot; changed preferences may deliberately change that count before a future frozen run.

Allowed platform differences: same-name login and attempted different-name login are machine-interface assertions for Python; the browser removes login controls after login and requires the confirmed reset flow to select another name. Browser startup/version and draft behavior use visible controls; Python origin binding and machine quit retain their command contract; desktop close, responsive editing, draft preservation, and confirmed reset are checked through actual Tk widgets. Normal restart/persistence, input validation, synchronization, retry, and deduplication remain required for both clients. Wire-only framing and concurrency checks target the shared server directly. AT-18 uses retained fixtures rather than a production model request; AT-15 supplies that separate real-generation evidence.

## Requirement traceability

| Requirement | Cases / evidence |
|---|---|
| REQ-GEN-01 | AT-15, AT-18, actual adapter command/model logs |
| REQ-GEN-02 | AT-15 with frozen input/test fingerprints |
| REQ-GEN-03 | Registered DIRECTORY/PRESENCE inputs, completed CHG-001–004 evidence in STATUS/CHANGES, unchanged generic harness/prompt |
| REQ-LOCAL-01 | AT-14; source/dependency review |
| REQ-ID-01 | AT-01, AT-09, AT-16 |
| REQ-SEND-01 | AT-02–AT-05, AT-11 |
| REQ-TEXT-01 | AT-02, AT-11, AT-14 |
| REQ-QUEUE-01 | AT-03, AT-04, AT-06, AT-09; optional OF-02 for forced write failure |
| REQ-STATE-01 | AT-03, AT-04, AT-07, AT-13; manual A04 observation |
| REQ-SYNC-01 | AT-06, AT-12, AT-13, AT-16 |
| REQ-RETRY-01 | AT-07, AT-13 |
| REQ-ORDER-01 | AT-06, AT-10 |
| REQ-DEDUPE-01 | AT-07–AT-10, AT-17 |
| REQ-RECEIVE-01 | AT-10, AT-13, AT-17; optional OF-01 |
| REQ-PERSIST-01 | AT-01, AT-09, AT-16 |
| REQ-FAILURE-01 | AT-11, AT-13, AT-16, AT-17; optional OF-02 |
| REQ-SESSION-01 | AT-13 cursor pause; explicit reset walkthrough; server source/protocol tests |
| REQ-UI-01 | AT-01, AT-02, AT-11, AT-14, AT-16; GUI-01–06; WEB-01; user M05 |
| REQ-SERVER-UI-01 | SG-01–SG-06 and AT-15 with the retained server GUI |
| REQ-DIR-01 | DIR-01, DIR-03–04, DIR-06–08 |
| REQ-RECEIPT-01 | DIR-02, DIR-05–08 |
| REQ-ACTIVITY-01 | DIR-03, DIR-05, DIR-08 |
| REQ-PRESENCE-01 | PRES-01–05 and AT-15 |
| REQ-WEB-UI-02 | WEB-01 and AT-15 |
| REQ-TEST-01 | All case reports and test-review evidence |
| REQ-RELEASE-01 | Provenance/history and archive restoration check described in TESTING.md |

## Manual sign-off, optional coverage, and evolution

For final user sign-off, complete the fixed walkthrough, queued restart check, and A04 usability inspection; record environment, time/revision, results, and evidence in M01–M06. These human observations are separate from automated cases. Blank fields remain pending and do not prevent Stage 2 implementation completion or creation of a review archive.

Optional OF-01 forcibly terminates a client around an incoming transaction to inspect crash atomicity. Optional OF-02 injects SQLite/IndexedDB write failures to verify failed enqueue dispatches nothing and failed receive advances no cursor. Their behavior remains required by the contract, but fault-injection execution is deferred and must be reported NOT_RUN unless actually exercised. Normal restart, malformed-page atomicity, and startup storage boundaries remain required baseline tests.

The authorized CHG-001–004 requirements below are cumulative parts of the current baseline. Their headings identify origin; they are already implemented requirements, not pending requests. Later selected changes must define their own specification delta and independent acceptance IDs, preserve applicable prior cases, and verify through unchanged generic harness/prompt logic. Do not import unselected FUTURE requests or instructional examples.

## CHG-001 desktop acceptance delta

These desktop cases remain required alongside the current protocol extensions. CHG-001 itself changed no wire behavior, shared extension or storage schema; CHG-003/004 subsequently added directory/receipt/presence requirements below. Freeze reconciled specs/tests before every generation run.

| ID | Required exercise and result |
|---|---|
| GUI-01 | Actual desktop login invalid/valid; visible identity/controls; invalid recipient, self-send, empty/oversized draft show errors and retain draft with no POST/outbox row; valid Unicode/newline text survives selection into detail panes. |
| GUI-02 | Repeat AT-03/04 fixed eight-step scenario using actual desktop controls against browser controls in both roles, with independent external API faults. Exact texts, FIFO observations and one displayed inbox row per message remain required. |
| GUI-03 | Close/reopen desktop with a queued row using the same store; preserve original ID/text/identity and deliver once on reconnect. Also open a specified version-1 pre-GUI fixture containing queued/accepted/failed rows, inbox and cursor; no migration/reset or data loss. |
| GUI-04 | Confirm/cancel GUI reset, preserve unrelated files, restore login/empty rows on success. Before resetting, the proxy must actually hold a GET response containing an old-identity message, with delivery still pending. Confirm reset during that held response; later delivery must not populate the new identity's inbox. |
| GUI-05 | During a delayed request edit a draft and inspect the window promptly; draft survives background refresh. Window close finishes within six seconds. Default main.py opens a GUI and stays alive with stdin closed. |
| GUI-06 | Unsupported store startup shows a visible error, leaves version/data unchanged, and offers a closable window. CURSOR_INVALID visibly disables sends; real permanent send failure shows failed plus reason. |

GUI tests run on a real Tk display, using an isolated Xvfb display in automated Linux runs. Missing Tk/display prerequisites are BLOCKED, never a skip or a successful machine-only substitute. GUI-01–06 belong to baseline verification and AT-15 clean regeneration. User M01–M06 remain separate final manual sign-off evidence.

## CHG-002 server desktop acceptance delta

REQ-SERVER-UI-01 maps to SG-01–SG-06. Tests use real Xvfb displays and production widgets, sockets/HTTP, and current generated clients. Preserve all applicable prior cases and the nine harness guards. These cases belong to --suite all and AT-15; missing display requirements are BLOCKED, never skipped.

| ID | Required exercise and result |
|---|---|
| SG-01 | Initial stopped controls; invalid port/missing assets fail visibly; correct inputs recover. GUI start exposes actual allocated loopback URL, health and browser assets; configuration and repeated Start disabled. Open browser receives the displayed URL (mock external browser launch only). |
| SG-02 | Real POST/GET, exact replay, conflict and invalid requests; UI counts unique messages, shows status/error responses and exact multiline Unicode detail. Monitoring does not consume a message or change deduplication/cursors. Latest-200 windows are bounded while full counts remain correct. |
| SG-03 | Stop closes the listener, clears live URL/monitoring and permits restart. New session ID and empty message store/counters, reusable port; warning explains fresh client stores. |
| SG-04 | Bind conflict does not stop the preexisting server; show actionable error and recover on a free port. Close during startup and while a request is incomplete finishes within six seconds and releases the listener. Ordinary startup with stdin closed opens the production window. |
| SG-05 | Start through actual GUI controls, then use actual Python desktop and browser clients to exchange greeting/reply and exact Unicode text. The monitor shows their accepted messages and details. Independently block each client's API for the full eight-step scenario, keeping this GUI-owned server alive; no duplicate deliveries. |
| SG-06 | While clients are attached, Stop makes the endpoint unavailable and new sends queue. Restart creates an empty session; explicitly fresh/reset both stores, then exchange new messages. Do not claim automatic recovery across a server restart. |

## CHG-003 directory and receipt acceptance delta

Preserve all applicable prior cases and nine harness guards. Record message-route history separately from directory/receipt traffic, scoping legacy send/page faults to the messages route while new cases inspect auxiliary attempts. This is deliberate extension coverage established before generation. DIR-01–08 map to REQ-DIR-01/REQ-RECEIPT-01/REQ-ACTIVITY-01 and belong to full verification and AT-15.

| ID | Required exercise and result |
|---|---|
| DIR-01 | HTTP users: empty start, valid/repeated announcements, sorted unique shared list, advisory presence expiry under controlled monotonic time, addressed never-announced users, strict schema/media/query/method errors, session reset. Invalid requests do not create users. |
| DIR-02 | HTTP receipts: GET does not acknowledge; valid/duplicate/older/concurrent cumulative reports are monotonic; invalid, boolean, out-of-range/ahead reports rejected without mutation; GET and acceptance receipts remain unchanged after acknowledgment. |
| DIR-03 | Real server Users controls: select/filter/refresh and inspect Sent/Received/Queued/counts/details, preserve read-only semantics, show offline-queue unknown notice; every per-user message remains inspectable beyond the global latest-200 window; Stop/Start clears selection/data. |
| DIR-04 | Both client GUI implementations: discover shared users, exclude self, filter, select a recipient without sending, preserve Unicode draft, send through normal controls, and converge with server directory. Manual unlisted recipients remain valid. |
| DIR-05 | GUI-managed server with each client as recipient: hold receipt reports while delivering a real message; durable inbox is populated but server still shows inbound Queued. Release reports and observe Received once, with Sent status updated. Inspect the original message fields and no read-status claim. |
| DIR-06 | For each client: malformed directory/rejected announcements/failed receipts do not block message send/receive; retain last valid directory and visible stale/error state; lost receipt acknowledgment retries safely; malformed receive pages never acknowledge an uncommitted cursor. |
| DIR-07 | For each client: reload/reopen with persisted inbox and a blocked receipt report; unblock and acknowledge existing cursor without duplicating inbox or migration. Reset during a held old-directory response; no old identity response restores cache/selection/draft into the new identity. Preserve legacy version-1 storage coverage. |
| DIR-08 | Offline client queued messages remain absent from server activity until actually accepted. Expired presence never deletes a user. Operator refresh/selection/filtering never causes delivery acknowledgment, user announcement, or message mutation. |


## CHG-004 cases

These cases belong to --suite all and AT-15 alongside all previous assertions. CHG-004 expanded the preceding 81 executable cases to 92; counts and repairs are historical evidence in STATUS/CHANGES.

| ID | Required exercise and result |
|---|---|
| PRES-01 | Strict presence schemas/routes, idempotent online/offline state, exact 15-second fallback, and explicit-offline latch immune to late heartbeats/messages/receipts/refresh. |
| PRES-02 | Real server Users status changes on presence HTTP without message traffic and preserves message/activity counts. |
| PRES-03 | Each GUI and Python machine control communicates Offline then Online without peer messages; offline queues remain intact and messages to an offline user cannot mark it online. |
| PRES-04 | Failed/lost notifications preserve local offline queues and report failure; no repeated offline traffic; reconnect recovers. |
| PRES-05 | Old in-flight heartbeat and rapid mode switches remain serialized; final intent wins without stale confirmation. |
| WEB-01 | Desktop panel geometry and semantic tables, exact text/details, keyboard selection and narrow-screen containment. |
