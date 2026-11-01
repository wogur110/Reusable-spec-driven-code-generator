# Product specification

Status: Stage 1 contract. Implementation and runtime verification are NOT_STARTED / NOT_RUN. Read [the decision record](../docs/DECISIONS.md) for effective choices and provenance.

## Your product choices

Edit only `Your input` to change a preference. Blank, whitespace-only, `TBD`, and `—` select the adjacent default. `false`, `0`, and `none` are explicit values subject to compatibility review. The technical requirements below are agent-maintained derived content.

<!-- USER:BEGIN PRODUCT_CHOICES -->
| ID | Question | Your input | Example / automatic default |
|---|---|---|---|
| P01 | What is the project called? | | `reusable-spec-driven-code-generator` |
| P02 | What should the project demonstrate? | | A reusable generator can recreate independent Python and TypeScript messaging clients from a precise specification. |
| P03 | Who will use or review it? | | A developer or reviewer running a small local demonstration on one computer. |
| P04 | What interfaces should the two clients have? | | Python command-line client and TypeScript desktop-browser client. |
| P05 | What should the browser screen contain? | | Username entry, recipient field, message input, Send button, inbox, outgoing-message list, and clear connection/status feedback. |
| P06 | How should identity work? | | Enter a username on first launch and remember it across normal restarts; use an explicit reset to change identity. No password. |
| P07 | What must survive a client restart? | | Username, queued messages with their original IDs, received messages, and synchronization progress. |
| P08 | Which offline experience is required? | | A running CLI or already-loaded page can queue messages while the API is unreachable; offline first load/reload of browser assets is excluded. |
| P09 | What send feedback should users see? | | `queued`, `accepted by server`, or `failed`, with an actionable error; server acceptance is not a read/delivery receipt. |
| P10 | What additional feature is essential? | | None beyond the project's required messaging behavior. |
| P11 | What is intentionally out of scope? | | Attachments, groups, reactions, passwords, cloud deployment, push notifications, closed-app delivery, and read receipts. |
<!-- USER:END PRODUCT_CHOICES -->

## Scope and operating assumptions

The deliverable is a configurable generation harness; local messaging demonstrates its behavior. Defaults resolve to Python CLI and plain TypeScript/HTML/CSS browser clients, independently implemented against [PROTOCOL.md](PROTOCOL.md). No extra feature or extension is active. [FUTURE.md](../FUTURE.md) starts empty.

One server process defines a demonstration session. One running client instance per username and one browser tab per identity are supported. Different clients use different identities and stores. There is no registration service, authentication, authorization, production hosting, or protection against impersonation. Client persistence assumes a writable store that the user/browser has not deleted or evicted. Network requests cannot guarantee exactly-once transmission.

## Resolved requirements

| ID | Required behavior | Source |
|---|---|---|
| REQ-GEN-01 | Generate working clients through an actual Codex invocation; source must not be restored from a prior implementation. Shared and platform-specific inputs are declared in configuration. | Source requirements; W01 |
| REQ-GEN-02 | Recreate both clients from retained inputs in a fresh workspace with no old client source or Git objects, and pass the same frozen acceptance tests. | Source requirements; P02 |
| REQ-GEN-03 | Permit explicitly registered specification extensions and selected targets without application-specific branches in generic orchestration. Record evolution execution separately; initially NOT_RUN. | Source requirements; guide Section 5 |
| REQ-LOCAL-01 | Application runtime and assets are local. Use a small in-memory Python server and no turnkey messaging SDK, external runtime service, or runtime CDN. | Source requirements; D02–D03 |
| REQ-ID-01 | Prompt for a username on first launch, persist it before use, restore on restart, and require explicit reset to change identity. Exact ASCII `[a-z][a-z0-9_]{0,31}`; no trimming or case conversion. | P06; derived validation |
| REQ-SEND-01 | Address a message to any valid different username, including a recipient who has never launched. No recipient registration check. | Source requirements; derived addressing |
| REQ-TEXT-01 | Accept 1–4,096 UTF-8 bytes of Unicode scalar text; preserve whitespace, newlines, and code points exactly. Whitespace-only text is valid. Reject lone surrogates, empty strings, and oversized text locally and on the server. | A03; derived limit |
| REQ-QUEUE-01 | Commit a new UUIDv4, immutable sender/recipient/text payload, and local FIFO order as queued before any send attempt. A failed enqueue produces no network send. | P07–P08 |
| REQ-STATE-01 | Persist queued, accepted, or failed state; present accepted as “accepted by server.” Accepted is not proof that a recipient received/read a message. Preserve failed rows and actionable reasons. | P09 |
| REQ-SYNC-01 | While active, serialize synchronization: one queued send followed by one incoming page; receive still runs after send failure. Use a one-second delay between finished cycles and a five-second total deadline per request. | Source requirements; derived scheduling |
| REQ-RETRY-01 | Retry uncertain/temporary outcomes with the same ID and payload; permanent rejection fails that entry and permits later queued entries to proceed. No automatic payload editing or ID replacement after transmission. | A02; P07 |
| REQ-ORDER-01 | Send queued entries in ascending local order. Display incoming entries by the recipient's server sequence. Different recipients have independent sequences; no global ordering promise. | Derived ordering |
| REQ-DEDUPE-01 | Within one server session, exact retries return the original receipt without creating another message. Persistently prevent duplicate inbox rows by sender and message ID. | A02 |
| REQ-RECEIVE-01 | Fetch contiguous recipient pages and commit inbox rows and cursor atomically. Validate an entire page before committing. Failure never skips uncommitted messages. | P07; derived durability |
| REQ-PERSIST-01 | Normal client restart retains identity, original pending IDs/payloads/order, accepted/failed outbox rows, inbox, and cursor. Unsupported store versions fail visibly without clearing data. | P07; A01 |
| REQ-FAILURE-01 | Invalid commands/drafts do not enqueue. Storage failures remain visible; acceptance-write failure leaves the original queued entry available for retry. Invalid receive pages leave storage unchanged. | A03; derived failure behavior |
| REQ-SESSION-01 | The server retains accepted messages for its process lifetime. After restarting it, explicitly reset demo client stores; automatic cross-session reconciliation is excluded. CURSOR_INVALID pauses synchronization until reset. | D04 |
| REQ-UI-01 | Both clients show incoming sender/exact text and outgoing recipient/text/state/error. Automatic synchronization must not block input. Browser uses the controls defined in TYPESCRIPT.md. | P04–P05; A04 |
| REQ-TEST-01 | Test actual clients, browser interactions, independent transport faults, reversed roles, and the fixed scenario. Observable transitions have 30-second deadlines; required tests cannot be skipped or weakened during repair. | Source requirements; A01–A05; W04 |
| REQ-RELEASE-01 | Record authorship separately from generated/retained ownership. Preserve real incremental commits, committed client source/locks, verification evidence, and an archive with restorable Git history. | Source requirements |

## Observable limits

The receive guarantee is one visible inbox row per `(sender,message_id)` under a continuing server session and intact local store, despite retries and normal restarts. It does not promise exactly-once network delivery, server crash recovery, or delivery after local state is lost. Messages accepted by the server remain available when their recipient is offline.

An already-loaded browser page can queue during an API outage; first load or reload requires its local assets to be reachable. Closed-tab/closed-process delivery and reliable background-tab timing are excluded. Reopening or activating a client resumes synchronization. Unknown wire fields are rejected until an extension is explicitly registered and reconciled. No labels, search, attachments, or group feature is selected.

Platform contracts: [PYTHON.md](PYTHON.md), [TYPESCRIPT.md](TYPESCRIPT.md). Requirement coverage: [ACCEPTANCE.md](ACCEPTANCE.md).
