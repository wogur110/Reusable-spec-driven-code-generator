# Resolved decisions

Reconciled on 2026-11-01 (America/Los_Angeles) for Stage 1. All 26 source preference cells are blank. Their effective values below come from the adjacent defaults, with provenance `TEMPLATE_DEFAULT`; none is represented as personally supplied by the user. The six manual observation cells remain blank and are not defaulted to successful results.

The user's explicit instructions authorize Stage 1 and standalone public framing. They do not authorize implementation in this turn. The supplied guide fixes Python and TypeScript as the two independent languages. [Project requirements](ASSIGNMENT.md) distinguishes source obligations from project choices.

## Effective preferences

Each row's source snapshot is a blank `Your input` cell. The linked source table remains the editable authority; this record is agent-maintained. Provenance for every row in this table is `TEMPLATE_DEFAULT`.

| ID | Effective value | Source / effect |
|---|---|---|
| P01 | Project name: reusable-spec-driven-code-generator. | [PRODUCT_CHOICES](../specs/PRODUCT.md#your-product-choices); documentation title/identity |
| P02 | Demonstrate recreating independent Python and TypeScript clients from precise specifications. | PRODUCT_CHOICES; REQ-GEN-01–03 |
| P03 | Developer/reviewer running a local demonstration on one computer. | PRODUCT_CHOICES; launch and review instructions |
| P04 | Python CLI and TypeScript desktop-browser client. | PRODUCT_CHOICES; platform contracts and actual-client tests |
| P05 | Username, recipient, text, Send, inbox, outgoing list, and connection/status feedback. | PRODUCT_CHOICES; TYPESCRIPT selectors, REQ-UI-01 |
| P06 | First-launch username, remembered across normal restarts; explicit reset to change it; no password. | PRODUCT_CHOICES; REQ-ID-01 |
| P07 | Persist identity, original queued IDs/payloads, received messages, and synchronization progress. | PRODUCT_CHOICES; REQ-PERSIST-01 |
| P08 | Running CLI/loaded page queues during API outage; offline browser asset load/reload excluded. | PRODUCT_CHOICES; REQ-QUEUE-01 and API-only reload faults |
| P09 | Show queued / accepted by server / failed with an actionable reason; acceptance is not delivery/read confirmation. | PRODUCT_CHOICES; REQ-STATE-01 |
| P10 | No additional feature. | PRODUCT_CHOICES; empty extension inventory and FUTURE queue |
| P11 | No attachments, groups, reactions, passwords, cloud deployment, push notifications, closed-app delivery, or read receipts. | PRODUCT_CHOICES; observable limits |
| A01 | Restart a queued client with the same store; reconnect; deliver original text once. Browser assets stay reachable. | [ACCEPTANCE_CHOICES](../specs/ACCEPTANCE.md#your-acceptance-expectations); AT-09 |
| A02 | Lose the reply after acceptance; retry without a second inbox entry. | ACCEPTANCE_CHOICES; AT-07–08 |
| A03 | Reject empty text/invalid recipients clearly; preserve valid Unicode, spaces, and newlines. | ACCEPTANCE_CHOICES; AT-02, AT-11 |
| A04 | Distinguish queued from accepted and read incoming sender/exact text without logs. | ACCEPTANCE_CHOICES; TESTING manual usability inspection |
| A05 | No extra user case beyond the fixed scenario, A01–A04, and derived boundary tests. | ACCEPTANCE_CHOICES; AT-01–18 |
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
| TD-03 | Versioned HTTP JSON send/retrieve endpoints, exact schemas, strict request validation, loopback default port 8765, same-origin assets/API. This keeps runtime local and removes CORS setup. | PROTOCOL; AT-14 |
| TD-04 | UUIDv4 client IDs, server dedupe key (sender, message_id), immutable payload, FIFO outbox, per-recipient sequence and persistent inbox dedupe. Lost replies can be retried safely within a server session. | PROTOCOL; AT-06–10 |
| TD-05 | Serialize one queued POST then one GET page even after a send failure; one-second cycle delay, five-second request deadline, 100-row pages, 32,768-byte request-body limit. Bound work while keeping input responsive. | PROTOCOL; AT-06, AT-10, AT-13–16 |
| TD-06 | SQLite version 1 and IndexedDB version 1 with atomic enqueue/outcome/receive transactions. Commit inbox and cursor together; reserve the maximum safe local allocator value as exhaustion. No baseline migration. | [PYTHON](../specs/PYTHON.md), [TYPESCRIPT](../specs/TYPESCRIPT.md); AT-09, AT-16–17 |
| TD-07 | Explicit identity reset; cursor-invalid pauses synchronization and new enqueue. Server restart always requires fresh/reset stores, even if a numeric cursor appears valid. No automatic session reconciliation. | PROTOCOL and platform reset contracts; AT-01, AT-13 |
| TD-08 | Standard-library threaded Python server with one lock protecting acceptance/dedupe/sequence snapshots; bounded HTTP framing and safe static-root access. Keep infrastructure small. | [DESIGN](../DESIGN.md), PROTOCOL; AT-08, AT-14 |
| TD-09 | Python JSON-lines interface uses production operations; browser tests use declared DOM controls and row attributes. Inspect stores only for persistence/atomicity assertions. No test-only acceptance implementation. | Platform contracts; AT-01–14, AT-16–17 |
| TD-10 | Python 3.10+ standard library; Node 22+ tooling; TypeScript 5.9.3, retained @playwright/test 1.56.1 and its Chromium. Exact planned package versions avoid floating dependency declarations; actual compatibility remains unverified. Trusted npm commands produce locks. | DESIGN dependency sources, TYPESCRIPT, [TESTING](../TESTING.md); Stage 2 setup/build evidence |
| TD-11 | Model selection remains null in baseline config until a successful Stage 2 harness-context request. Inspect installed CLI help; choose a working authenticated tool/model without assuming entitlement from a model name. | [GENERATE](../GENERATE.md); authentication/model access UNVERIFIED |
| TD-12 | Fresh allowlisted candidate workspaces, separate target context, retained inventory/hash checks after agent calls and trusted checks, and rollback publication. Previous clients never become generation context. | GENERATE; AT-15, AT-18 |
| TD-13 | Generic prompt/config-driven orchestration; extensions initially empty. Maximum four calls per target, 600 seconds per generation call, 5,400 seconds per harness run, and a 7,200-second outer clean-check budget. Do not add application feature branches to orchestration. | GENERATE complete timeout table; AT-18; evolution NOT_RUN |
| TD-14 | Independent retained assertions drive actual clients through external per-client API faults. Baseline suite, harness guards, and outer clean regeneration are separate to avoid recursion; manual facts remain user-owned. | ACCEPTANCE and TESTING; AT-01–18, M01–M06 |
| TD-15 | Record authorship separately from retained/generated ownership, preserve authentic commits, and verify archive inventory/history restoration. Track implementation, manual review, deferred evolution, and final readiness independently. | DESIGN, TESTING, [STATUS](STATUS.md), [review record](ASSIGNMENT_REVIEW.md) |

## Observation and reconciliation snapshot

Source snapshot: P01–P11, A01–A05, D01–D05, and W01–W05 all blank as of this revision. M01, M02, M05, and M06 are `NOT_RECORDED`; M03 and M04 are `NOT_RUN`. These states describe missing evidence, not preferences. Current requirements contain no unresolved user-choice conflict. Environment/model uncertainty is a Stage 2 prerequisite, not a missing Stage 1 protocol decision.

After a user edit, compare the changed source cell against this snapshot, preserve its exact wording, and reconcile affected decisions, requirements, platform schemas, tests, and instructions before implementation. Blank/whitespace, TBD, and — mean the adjacent default; false, 0, and none are explicit values whose compatibility must be checked. Do not overwrite source cells with resolved values.

Unchanged blanks do not revoke a later explicitly authorized extension or selected change request. Record that authorization, its affected source values and previous values, and the resulting current contract. Archive completed requests in [CHANGES](CHANGES.md); leave unrelated inputs and requests intact. A changed UI or coding-tool preference may require broad reconciliation, but does not itself authorize Stage 2. The five editable source locations are listed in [README](../README.md#what-you-can-edit).
