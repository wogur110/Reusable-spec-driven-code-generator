# Resolved decisions

Current decisions include completed CHG-001–004 and explicit P01 project name `Jaehyeok-spec-driven-code-generator`. The other 25 preference inputs remain blank. After regeneration, the user supplied M01–M05; M06 remains blank. Current defaults reflect those decisions; previous values and provenance remain historical. Actual all-client regeneration `20261102T002927228257Z`, published-checkout acceptance, and independent clean proof `20261102T010021541172Z` passed against the reconciled contract.

The user's Stage 2 and CHG-001–004 requests authorized the completed behavior. The current request authorizes reconciling edited USER choices, regenerating both clients through the harness and verifying clean regeneration. Standalone public framing remains in force. Python and TypeScript stay independent; [project requirements](ASSIGNMENT.md) distinguishes source obligations from project choices.

## Effective preferences

P01 has the explicit source value below; all other preference inputs are blank. Linked forms remain editable, and this record is agent-maintained. TEMPLATE_DEFAULT applies unless a row identifies a later USER_EXPLICIT request or AGENT_DERIVED reconciliation. Updating adjacent examples does not rewrite historical provenance.

| ID | Effective value | Source / effect |
|---|---|---|
| P01 | Project name: Jaehyeok-spec-driven-code-generator. | USER_EXPLICIT: P01; [PRODUCT_CHOICES](../specs/PRODUCT.md#your-product-choices); project documentation identity, preserving technical compatibility identifiers |
| P02 | Demonstrate recreating independent Python and TypeScript clients from precise specifications. | PRODUCT_CHOICES; REQ-GEN-01–03 |
| P03 | Developer/reviewer running a local demonstration on one computer. | PRODUCT_CHOICES; launch and review instructions |
| P04 | Python Tkinter desktop GUI, retained headless machine interface, and TypeScript browser with comparable compact desktop layout. | USER_EXPLICIT: CHG-001/004; PRODUCT_CHOICES, platform contracts |
| P05 | Session/transport/reset and presence controls, filterable recipients/Refresh, compose/Send, and side-by-side Inbox/Outgoing tables with exact detail panes; stack history on narrow screens. | USER_EXPLICIT: CHG-003/004; layout/selectors AGENT_DERIVED in TYPESCRIPT |
| P06 | First-launch username, remembered across normal restarts; explicit reset to change it; no password. | PRODUCT_CHOICES; REQ-ID-01 |
| P07 | Persist identity, original queued IDs/payloads, received messages, and synchronization progress. | PRODUCT_CHOICES; REQ-PERSIST-01 |
| P08 | Desktop/loaded page queues offline; one final bounded notification on Offline selection, then no API traffic; reconnect resumes work. Offline asset load/reload remains excluded. | AGENT_DERIVED from CHG-001/004; PRODUCT_CHOICES, PRESENCE |
| P09 | Show queued / accepted by server / failed with an actionable reason; acceptance is not delivery/read confirmation. | PRODUCT_CHOICES; REQ-STATE-01 |
| P10 | Retained server GUI, shared recipient discovery, click-to-address, durable receipt/activity views, and explicit presence with heartbeat fallback; offline client queues unknown. | USER_EXPLICIT: CHG-002–004; SERVER defines retained behavior; DIRECTORY/PRESENCE are registered for both clients |
| P11 | No attachments, groups, reactions, passwords, cloud deployment, push notifications, closed-app delivery, or read receipts. | PRODUCT_CHOICES; observable limits |
| A01 | Restart a queued client with the same store; reconnect; deliver original text once. Browser assets stay reachable. | [ACCEPTANCE_CHOICES](../specs/ACCEPTANCE.md#your-acceptance-expectations); AT-09 |
| A02 | Lose the reply after acceptance; retry without a second inbox entry. | ACCEPTANCE_CHOICES; AT-07–08 |
| A03 | Reject empty text/invalid recipients clearly; preserve valid Unicode, spaces, and newlines. | ACCEPTANCE_CHOICES; AT-02, AT-11 |
| A04 | Distinguish queued from accepted and read incoming sender/exact text without logs. | ACCEPTANCE_CHOICES; TESTING manual usability inspection |
| A05 | Fixed scenario, A01–A04, derived boundaries and all completed GUI/server/directory/receipt/presence/web-layout cases; no pending feature selected. | AGENT_DERIVED from CHG-001–004; AT, GUI, SG, DIR, PRES and WEB acceptance IDs |
| D01 | Prioritize offline correctness, clean regeneration, readable specs, simplicity, then polish. | [DESIGN_CHOICES](../DESIGN.md#your-design-priorities); design tradeoffs |
| D02 | One local Python server process with in-memory state; no database/authentication service. | DESIGN_CHOICES; REQ-LOCAL-01, REQ-SESSION-01 |
| D03 | Prefer standard libraries and small general-purpose tools; no turnkey messaging SDK or runtime CDN. | DESIGN_CHOICES; dependency policy |
| D04 | Delivery guarantees require the same running server; explicitly use fresh client stores after restart. | DESIGN_CHOICES; PROTOCOL session boundary and TESTING reset |
| D05 | Prefer understandable simplicity; generalize where necessary for the generation harness. | DESIGN_CHOICES; config-driven targets and simple example clients |
| W01 | Invoke Codex. Claude Code remains a permitted alternative after reconciling affected setup. | [WORKFLOW_CHOICES](../AGENTS.md#your-working-preferences); GENERATE adapter |
| W02 | Verify a noninteractive request with a model available to the actual CLI/account; record tool/requested/effective model, using UNREPORTED when needed. | WORKFLOW_CHOICES; Stage 2 prerequisite; no model assumed available |
| W03 | Resolve routine choices with a minimal compatible design; ask only for genuine conflicts or missing user-only facts. | WORKFLOW_CHOICES; this record and scope control |
| W04 | Initial generation plus at most three repairs per client; 30 seconds per observable transition and separate tool/build deadlines. | WORKFLOW_CHOICES; GENERATE execution bounds |
| W05 | Brief milestone updates with actual results, blockers, and next steps. | WORKFLOW_CHOICES; progress and evidence reporting |

## Derived technical choices

Every TD row has provenance `AGENT_DERIVED`. These choices resolve implementation details; they are not additional user answers. Exact schemas and procedures live in the linked contracts.

| ID | Decision and reason | Authoritative detail / verification |
|---|---|---|
| TD-01 | Exact lowercase ASCII usernames, 1–32 characters, no normalization; one instance per identity. Simple addressing avoids cross-language normalization ambiguity. No passwords or recipient registration. | [PRODUCT](../specs/PRODUCT.md), [PROTOCOL](../specs/PROTOCOL.md); AT-01, AT-05, AT-11 |
| TD-02 | Unicode scalar text of 1–4,096 UTF-8 bytes, including whitespace-only text; no trimming. A byte limit makes both languages agree. | PROTOCOL; AT-02, AT-11 |
| TD-03 | Version-1 HTTP JSON messaging, directory, durable-receipt and presence routes with exact schemas and strict validation; loopback port 8765, same-origin assets/API. | PROTOCOL, DIRECTORY, PRESENCE; AT-14, DIR-01–02, PRES-01 |
| TD-04 | UUIDv4 client IDs, server dedupe key (sender, message_id), immutable payload, FIFO outbox, per-recipient sequence and persistent inbox dedupe. Lost replies can be retried safely within a server session. | PROTOCOL; AT-06–10 |
| TD-05 | One serialized scheduler prioritizes presence intent, then queued POST/GET and receipt/heartbeat/directory work. One-second cycle delay, five-second message and two-second auxiliary deadlines; at most 18 seconds of network work with an online presence attempt. 100-row pages; 32,768-byte request-body limit. | PROTOCOL, DIRECTORY, PRESENCE; AT-06, AT-10, AT-13–16, DIR-06–07, PRES-03–05 |
| TD-06 | SQLite version 1 and IndexedDB version 1 with atomic enqueue/outcome/receive transactions. Commit inbox and cursor together; reserve the maximum safe local allocator value as exhaustion. No baseline migration. | [PYTHON](../specs/PYTHON.md), [TYPESCRIPT](../specs/TYPESCRIPT.md); AT-09, AT-16–17 |
| TD-07 | Explicit identity reset; cursor-invalid pauses synchronization and new enqueue. Server restart always requires fresh/reset stores, even if a numeric cursor appears valid. No automatic session reconciliation. | PROTOCOL and platform reset contracts; AT-01, AT-13 |
| TD-08 | Standard-library threaded Python server with one lock protecting acceptance/dedupe/sequence snapshots; bounded HTTP framing and safe static-root access. Keep infrastructure small. | [DESIGN](../DESIGN.md), PROTOCOL; AT-08, AT-14 |
| TD-09 | Python GUI tests operate declared production Tk widgets; JSON-lines tests use the same production operations. Browser tests use declared DOM controls and row attributes. Inspect stores only for persistence/atomicity assertions. No test-only acceptance implementation. | Platform contracts; AT-01–14, AT-16–17 |
| TD-10 | Python 3.10+ standard library; Node 22+ tooling; TypeScript 5.9.3, retained @playwright/test 1.56.1 and its Chromium. Exact package versions and actual npm locks avoid floating declarations; the selected versions pass builds and the acceptance suite. | DESIGN dependency sources, TYPESCRIPT, [TESTING](../TESTING.md); Stage 2 setup/build evidence |
| TD-11 | Project-local Codex 0.166.0 with requested gpt-6-astra passed writable authenticated preflight and actual generation; effective model is UNREPORTED. Recheck access in each harness run. | [GENERATE](../GENERATE.md); authenticated preflight and generation PASS |
| TD-12 | Fresh allowlisted candidate workspaces, separate target context, retained inventory/hash checks after agent calls and trusted checks, and rollback publication. Previous clients never become generation context. | GENERATE; AT-15, AT-18 |
| TD-13 | Generic prompt/config-driven orchestration; DIRECTORY.md then PRESENCE.md registered for both targets. Maximum four calls per target, 600 seconds per call, 5,400 seconds per harness run and 7,200 seconds per clean proof. No feature-specific orchestration branches. | GENERATE timeout table; AT-18 and recorded CHG-001–004 evolution |
| TD-14 | Independent retained assertions drive actual clients under external per-client API faults. Current acceptance includes completed GUI/server/directory/presence/layout cases. Harness guards and clean proof remain separate to avoid recursion; manual facts remain user-owned. | ACCEPTANCE and TESTING; AT, GUI, SG, DIR, PRES, WEB, M01–M06 |
| TD-15 | Record authorship separately from ownership; preserve real commits and archive history restoration. Track implementation, manual review, future unexecuted work and current packaging independently. | DESIGN, TESTING, STATUS and review record |

## Observation and reconciliation snapshot

Source snapshot: P01 is exactly `Jaehyeok-spec-driven-code-generator` (raw table-cell formatting preserved); P02–P11, A01–A05, D01–D05 and W01–W05 remain blank. All manual fields were blank during regeneration. The user subsequently recorded M03/M04 PASS and M05 Good, with Windows 11 mentioned in M01 and `11/1/2026, 9:20pm` in M02. Actual browser/version, tested revision and M06 evidence are not supplied. No unresolved choice conflict. Native/browser readiness and authenticated model access passed in the generation and clean-proof environment; other platforms/accounts have no equivalent automated verification.

Every regeneration request includes comparing current preference cells against this snapshot. Preserve exact user wording. Reconcile changed choices into decisions, contracts, independent tests and necessary retained implementation/configuration before freezing inputs. With no changed choices, use the current contract unchanged. Blank/whitespace, TBD and — select adjacent current defaults; false, 0 and none are explicit choices. Never fill source cells with resolved values. Candidate-generation and repair agents cannot perform this parent reconciliation or modify frozen inputs.

Unchanged blanks do not revoke completed changes. Saving preferences alone starts no work; a regeneration request includes reconciliation by default and does not restart Stage 1. FUTURE.md requires separate explicit selection/application. Preserve historical requests and runtime evidence; record previous/new values when choices change. Manual fields remain factual observations. See the [README default instruction](../README.md#default-regeneration-instruction).

## P01 reconciliation and requested regeneration

State: COMPLETE — published generation `20261102T002927228257Z` and checkout verification each passed 92/92; guards passed 9/9. Clean proof `20261102T010021541172Z` passed 92/92 inside the harness and standalone while preserving the original tree. Published generation used three calls per target; the clean proof used one per target.

| Field | Previous source input / effective default | Current source input / adjacent default | Provenance |
|---|---|---|---|
| P01 | Blank / `reusable-spec-driven-code-generator` | `Jaehyeok-spec-driven-code-generator` / `Jaehyeok-spec-driven-code-generator` | USER_EXPLICIT input; default synchronized by the parent agent |

P01 changes the project documentation identity. Existing paths, package/storage identifiers, window titles, selectors, schema versions and message behavior remain the CHG-004 contract; this is not a repository or data migration. The parent updated the README title, product identity/default, current decision snapshot and operating/evidence summaries. No other default column changes are needed. All user-authored cell text and manual observations are preserved.

Retained test impact: no messaging/UI/storage assertions changed for this documentation name choice. The existing 92-case contract and nine guards remained frozen. Both clients were actually regenerated from the updated registered inputs, then passed published-checkout and independent clean verification. Generic runner, prompt, configuration and retained server remain unchanged. No pending FUTURE request or prior client source entered candidate context. This direct request creates no CHG entry. The TypeScript build conflict and first 91/92 acceptance failure remain recorded; ordinary bounded repairs changed only candidates.

## Current-default documentation reconciliation

For future authorized development, maintain this decision record alongside affected specifications and preference-table defaults. Record each changed default's field ID, previous/new text, rationale and authorizing request before generation input freeze. Preserve exact user input values and historical snapshots. Verify default/spec/code/doc consistency before completion, and explain when no default change is needed; see [the agent rule](../AGENTS.md#future-development-completion-rule).

At the user's request, the adjacent examples for P04, P05, P08, P10 and A05 now describe the already completed baseline. The original questions, IDs, all input values and manual observation fields are preserved. This is a documentation correction, not a newly implemented feature or a new CHG request. Previous example/default text is retained here so a future reconciliation can distinguish user edits from changes to derived guidance.

| ID | Previous adjacent example/default | Basis for current default |
|---|---|---|
| P04 | Python command-line client and TypeScript desktop-browser client. | CHG-001/004; current value above |
| P05 | Username entry, recipient field, message input, Send button, inbox, outgoing-message list, and clear connection/status feedback. | CHG-003/004; current value above |
| P08 | A running CLI or already-loaded page can queue messages while the API is unreachable; offline first load/reload of browser assets is excluded. | CHG-001/004; current value above |
| P10 | None beyond the project's required messaging behavior. | CHG-002–004; current value above |
| A05 | None beyond the fixed scenario, A01–A04, and the technical boundary tests derived by the agent. | Acceptance derived from CHG-001–004; current value above |

The construction guide's original bootstrap catalog remains labeled as historical starting defaults. For this completed checkout, current preference forms and registered contracts govern regeneration. The following sections retain decisions and outcomes at the time each implementation change was made; later completed changes supersede their earlier scope statements.

## Stage 2 environment reconciliation

On 2026-11-01, the agent verified project-local Codex 0.166.0 with requested model gpt-6-astra using the current signed-in account. A noninteractive request completed and wrote its required probe file; effective model is UNREPORTED. This resolves TD-11 without filling W02. CLI dependency manifests/locks live in generator/codex/. Installed Playwright browser binaries use /tmp/reusable-spec-playwright by default (PLAYWRIGHT_BROWSERS_PATH can override it); this cache contains upstream tools only. All 26 preference cells remain unchanged.

On the first actual generation, the 42-test baseline passed, but an additional black-box review reproduced a Python receive failure for a valid 2,468,923-byte JSON page. The protocol now states explicitly that request and response limits differ and that a capped receiver must accommodate the full page (at least 4 MiB). AT-10 adds this regression for both clients. This strengthens coverage of existing text/page limits; it is not a feature extension or a repair-loop assertion change. Browser redirect errors are also clarified because fetch redirect:error cannot distinguish them from other TypeError transport failures. Unknown HTTP methods now follow the existing 405 route contract. The subsequent generator run freezes these revised inputs; no generated source is manually patched.

## CHG-001 decisions and verified outcome

The selected request explicitly replaces the human Python CLI with a desktop GUI. Preserve all source USER cells verbatim, including blank P04/P08; record their original effective CLI wording in the completion archive. P04 now resolves from CHG-001 (`USER_EXPLICIT`), P08's running-client interpretation follows it (`AGENT_DERIVED`). This later authorization supersedes guide defaults, not unrelated preferences.

Choose tkinter/ttk with Tcl/Tk 8.6 to retain Python's no-pip policy. Add documented native prerequisites and Xvfb GUI automation; these are OS/tool dependencies, not messaging SDKs or external runtime services. Both frontends keep independent production messaging code. Preserve SQLite version 1 and the display-free --machine protocol interface. Desktop controls, details, confirmation, and close behavior are specified in PYTHON; GUI-01–06 add actual-widget acceptance. Browser behavior, server, protocol, generic orchestration and prompt remain unchanged. Existing extensions stay empty; this is a revision of the registered Python/shared contracts.

CHG-001 is complete: 55 acceptance cases and nine guard tests pass; clean proof 20261101T151017779910Z recreated both clients and passed the same 55 cases twice. The earlier failed proof and retained-fixture correction are preserved in CHANGES/EVIDENCE. Source forms remain unchanged. Native Tk 8.6.12 and Ubuntu GUI packages are verified; user manual sign-off remains pending.

## CHG-002 — retained server desktop

USER_EXPLICIT: CHG-002 adds local graphical Start/Stop/monitoring to the existing retained server. All source preferences and observations remain unchanged. AGENT_DERIVED: reuse standard-library Tkinter/ttk, bind loopback only, keep the terminal entry point, and use one in-process Server instance per GUI Start/Stop session. Bound request/message display windows to 200 and expose exact selected text. Running-server session lifetime replaces the process-lifetime shorthand when the GUI is used; each restart still requires fresh client stores. Details are in specs/SERVER.md. Client wire/storage/UI contracts do not change, so no targeted client regeneration is required. The expanded full suite and real clean regeneration validate continued compatibility. Generic generator configuration, orchestration and prompt remain unchanged.

## CHG-003 — shared directory and honest receipt observations

USER_EXPLICIT: apply CHG-003 after the verified CHG-001/002 GUIs. The user clarified: “Show server-accepted messages awaiting recipient acknowledgment as queued; label offline client queues as unknown.” P10 remains blank; this later request adds the feature. All source USER cells are preserved. AGENT_DERIVED: known usernames persist for a server session, with a 15-second advisory heartbeat window; valid manual recipients need not be listed. Cumulative receipts report durable receive cursors, never read status, and require no client storage migration. Queued is inbound pending receipt for the selected user; Sent also shows each outgoing message’s queued/received status. Directory and receipt failures cannot block messaging. Register DIRECTORY.md for both targets and regenerate both through the unchanged generic harness/prompt. No client-outbox telemetry or administrative mutation is selected.


CHG-004 (USER_EXPLICIT): the web UI should resemble the Python GUI and selecting Offline/Online should communicate with the server, without another user sending a message. Derived choices: compact desktop layout with table/details; a separate two-second presence control request serialized ahead of normal work; explicit-offline latch defeats late legacy heartbeats; one final offline attempt and no further offline traffic; 15-second heartbeat fallback for actual connectivity loss. Existing schemas and USER cells remain unchanged. Multiple active clients sharing a username remain outside the supported demo precondition.
