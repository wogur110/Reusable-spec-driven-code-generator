# Design and ownership

Status: completed CHG-004 design preserved after P01 reconciliation and both-client regeneration. Current published and clean-proof acceptance each passed 92 cases, with nine harness guards passing. Clean proof `20261102T010021541172Z` preserved the original tree. [Decisions](docs/DECISIONS.md) records current defaults/provenance; [status](docs/STATUS.md) separates actual runs, earlier failures and pending manual/packaging work.

## Your design priorities

Leave preferences blank to use the adjacent defaults. These fields express priorities; the agent maintains the technical design below.

<!-- USER:BEGIN DESIGN_CHOICES -->
| ID | Question | Your input | Example / automatic default |
|---|---|---|---|
| D01 | What is the priority order? | | Correct offline behavior, clean regeneration, readable specifications, implementation simplicity, then visual polish. |
| D02 | How much server complexity is acceptable? | | One local Python process with in-memory state; no server database or authentication service. |
| D03 | What dependency policy should guide the agent? | | Prefer standard libraries and small general-purpose tools; no turnkey messaging SDK and no runtime CDN. |
| D04 | What reliability limitation is acceptable? | | Delivery guarantees apply within one continuously running server session; restart the demo with explicit fresh client stores after server restart. |
| D05 | What tradeoff should resolve routine design choices? | | Prefer a small understandable solution over a reusable abstraction unless the abstraction is necessary for the code-generation harness. |
<!-- USER:END DESIGN_CHOICES -->

## Architecture and principles

Project identity is `Jaehyeok-spec-driven-code-generator` (P01). Existing application titles, storage/package identifiers and output paths retain their compatibility contracts; this documentation name change introduces no architecture or data migration.

Current registered specs determine behavior; independent retained tests establish expectations before generation. A regeneration request first reconciles changed USER choices against the decision snapshot. Completed features remain unless those choices intentionally change them; FUTURE.md stays outside generation scope. The generic harness freezes registered Markdown/configuration, invokes the coding tool, validates isolated candidates and publishes only after checks. It owns paths, execution, integrity and evidence, with no messaging logic or finished client templates.

```mermaid
flowchart LR
  S[Shared and platform specifications] --> H[Retained generation harness]
  H --> P[Independent Python candidate]
  H --> T[Independent TypeScript candidate]
  P --> V[Trusted build and acceptance checks]
  T --> V
  R[Retained server and tests] --> V
  V --> O[Validated generated source]
```

At runtime, each client has presentation, validation, durable storage, transport, and one synchronization scheduler. Python uses standard-library HTTP and SQLite with short locked transactions; the browser uses fetch and IndexedDB. They share written schemas and tests, not implementation modules. One retained Python HTTP server serves browser files and maintains in-memory streams/receipts under one lock. HTTP polling is sufficient for the small local scope and keeps transport faults observable.

Durable enqueue precedes network dispatch. Stable IDs let the server distinguish retries from new submissions. The server stores accepted messages for its entire session; retrieval is nondestructive, so an interrupted receiver can retry before committing a cursor. A single client receive transaction preserves inbox/cursor consistency. Each recipient has a contiguous sequence; local outgoing order is independent of server sequence. Outgoing accepted means server acceptance only.

One scheduler prioritizes presence intent, then sends one queued message and retrieves one page, followed by durable receipt, heartbeat and directory work. Message deadlines are five seconds; auxiliary/presence deadlines are two seconds, with one second between cycles. Offline selection stops ordinary work but allows one final bounded notification. Network work never holds a local storage lock or blocks the UI. Identity/reset and mode-revision guards prevent stale replies from restoring old state.

## Tradeoffs and boundaries

| Decision | Benefit | Limit |
|---|---|---|
| In-memory server | Small, auditable protocol implementation | Every new session, including GUI Stop/Start, requires fresh/reset client stores; no durable server recovery |
| Polling HTTP/JSON | Simple independent clients and fault injection | Foreground latency and background browser scheduling limitations |
| SQLite / IndexedDB | Native durable local queues | Storage denial/eviction and disk failure cannot be eliminated |
| One active identity instance | Avoids account/multi-device coordination | Shared-tab or multi-device concurrency is unsupported |
| Exact schemas and byte limits | Consistent cross-language boundaries | Extensions must be explicitly specified and registered |
| Independent retained tests | Common behavior checked without shared client code | Optional forced-crash/write-failure paths remain unverified until exercised |
| Staged publication | Failed generations preserve usable source | Requires disposable workspaces and integrity manifests |

No authentication, production security, network exactly-once guarantee, server database, push notifications or offline browser asset cache is included. Current completed scope includes directory, durable receipts, explicit presence and desktop interfaces; later changes require edited USER choices plus reconciliation or a separately selected [FUTURE.md](FUTURE.md) request. Completed requests are archived in [CHANGES](docs/CHANGES.md).

## Dependency rationale

Python 3.10+ standard libraries cover server, harness, SQLite client, and unittest. Node.js 22+ runs build/test tooling. Select exact TypeScript 5.9.3 and retained `@playwright/test` 1.56.1 with its matching Chromium for a reproducible compiler/browser test pair. Their upstream releases exist; the selected compiler/browser pair is installed and the expanded baseline passes. See [TypeScript release](https://github.com/microsoft/TypeScript/releases/tag/v5.9.3) and [Playwright release](https://github.com/microsoft/playwright/releases/tag/v1.56.1).

Real package-manager locks are committed; tested versions are recorded in STATUS. The generation CLI is a separate development dependency; select and pin a version only after an authenticated readiness check in the harness environment. Do not infer current account access from installed binaries or successful work in another project. The desktop requires native tkinter/Tcl/Tk packages; retained GUI tests require Xvfb and X11 utilities. No pip package or cloud messaging service is required. README and TESTING list the exact Ubuntu/WSL installation command.

## Authorship and regeneration ownership

| Artifact | Ownership boundary | Actual authorship/evidence |
|---|---|---|
| Instruction_for_Agent.md | Retained construction guide | User-supplied guide revised by the agent with user authorization; commit 216ef72 |
| Root docs, specs/, docs/ | Retained contracts and workflow | Agent-authored in Stage 1 and reconciled with actual Stage 2 implementation/evidence; no user field values were invented |
| USER preference cells | User-owned inputs | P01 explicitly names Jaehyeok-spec-driven-code-generator; 25 preferences remain blank; current/previous defaults and provenance in DECISIONS |
| M01–M06 | User-owned factual observations | M01–M05 supplied by the user; offline/restart PASS and usability Good. M06 remains blank; detailed browser/version and tested revision are not supplied. |
| generator/, server/, tests/, scripts/ | Retained during client generation | Parent coding agent authored retained infrastructure/tests; actual commits record milestones |
| generated/python-client/, generated/typescript-web/ | Deletion/regeneration boundaries | Separate actual Codex harness calls; Python regenerated for the page-limit regression/CHG-001 and both clients for CHG-003/004; recorded tool/model in STATUS |
| Dependency locks / compiled assets | Locks committed / builds disposable | npm created committed locks; TypeScript/Node produced disposable browser assets |

Retained does not mean human-written. Do not invent authors, dates, commits, verification runs, or an old project lineage. Stage 2 records actual commands, input/test hashes, repairs, and generated source provenance. A release archive includes authentic history and excludes credentials, stores, caches, and old source-bearing transcripts; verify restoration before marking archive completion.

## Desktop presentation (CHG-001)

Tkinter/ttk supplies the Python desktop window. The GUI and retained --machine interface use the same generated Python messaging core; the browser implementation remains independent. Tk owns the main thread, while one bounded synchronization worker exchanges committed snapshots through scheduled UI updates. SQLite version 1 remains compatible with pre-GUI stores. Actual-widget tests complement existing machine protocol tests. Native Tcl/Tk and automated Xvfb prerequisites are installed/reported separately from Python packages. Evolution verification must preserve generic orchestration/prompt hashes and regenerate from the revised specifications; CHG-001 execution passed, with exact fingerprints and commands in [CHANGES](docs/CHANGES.md).

## CHG-002 retained server control window

The optional server/gui.py Tkinter window owns one retained Server per Start/Stop session. Binding, serving, and shutdown run outside the Tk event loop; widget updates occur only on that loop. Locked bounded snapshots expose recent responses and accepted messages without affecting protocol state. Each new instance starts empty, including restarts inside the same GUI process. This management UI is retained parent-agent code, not generated client code. See [the server contract](specs/SERVER.md).

## CHG-003 directory and receipt design

One retained Store lock protects accepted messages, session-known users, heartbeat times, explicit-offline latches and cumulative recipient acknowledgments. Clients serialize presence transitions and normal send/receive/receipt/heartbeat/directory work; only committed receive cursors may be acknowledged. The server GUI observes the same locked state. No schema migration or per-message client receipt table is needed. Transient caches use identity/reset guards and do not prevent manual sending. Server activity reports durable receipt, while unseen offline outboxes remain unknown. Exact contracts are in [DIRECTORY.md](specs/DIRECTORY.md) and [PRESENCE.md](specs/PRESENCE.md).


## CHG-004 presence and browser presentation

CHG-004 separates local transport intent from confirmed server presence. A serialized priority control request communicates mode changes; explicit offline cannot be undone by messages or late heartbeats. Failed Offline notification preserves queues and uses 15-second expiry as fallback. The browser follows the desktop task layout with bounded panels, keyboard-selectable tables and exact text details; narrow layouts stack history. Both clients retain version-1 stores and independent messaging implementations.
