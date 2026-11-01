# Instructions for the Coding Agent

This is the construction guide for a reusable, spec-driven code generator. The example application uses independent Python and TypeScript messaging clients. All project documentation, interface labels, and code comments must be in English.

**Use this file as a structure and requirements guide. It contains no complete output-document bodies to copy or extract.** In Stage 1, author the Markdown documents described below. In Stage 2, implement the generator, server, tests, and generated clients from the completed specifications. The user needs only this instruction file to begin.

Keep the canonical filename `Instruction_for_Agent.md`, including its capitalization. This file does not execute itself: the user must explicitly request the work they want their coding agent to perform. The generated `README.md` is the public operating guide for the code generator; this file is the guide for constructing it.

Use standalone project framing in public documentation, interface labels, comments, and reports. Do not name a commissioning company or describe the project as a commissioned assignment. Use neutral requirements and review language while preserving the technical obligations and truthful source provenance described in Section 2.

The project root is the directory containing this file. Keep project edits, Git operations, and published outputs within that root; disposable workspaces may be created under its `artifacts/` directory or a documented temporary directory. Leave sibling projects and their history unchanged. An explicitly supplied external requirements file is a read-only reference, not authorization to modify its location or copy another project's implementation into this one.

## 1. The two-stage workflow

| Step | Actor | Action |
|---|---|---|
| Stage 1 | Agent | Create every required Markdown document from this guide, resolve defaults, and complete the technical specifications. Create editable USER sections. Stop before implementation. |
| Review | User | Read README's edit map and the resolved decisions. Change any USER preference cells, or leave them blank to use their adjacent defaults. |
| Stage 1 revision, if needed | Agent | Reconcile edited inputs with all affected specifications and planned tests. This is a revision within Stage 1, not another implementation stage. |
| Stage 2 | Agent | Check the current inputs and specifications, implement the retained components, generate both clients through the harness, test, and verify clean regeneration. Record implementation completion separately from pending user review. |
| Manual verification | User | Run the documented walkthrough and record actual observations in TESTING.md. |

An explicit construction or bootstrap request without a stage defaults to Stage 1. Requests to read, analyze, or review do not authorize file changes or stage execution. A request to revise this guide authorizes those edits only; it does not start either stage. Do not switch to Stage 2 merely because documents are complete. An explicit Stage 2 request authorizes implementation and routine supporting corrections; it does not require repeated approval for each technical choice.

### Stage 1 instruction the user can send

```text
Read Instruction_for_Agent.md and execute Stage 1.
Create all required Markdown documents from its structure and content requirements.
Preserve existing USER inputs. Resolve blank preferences using the adjacent defaults.
Write complete technical specifications, acceptance cases, and planned procedures.
Show me the USER sections I can edit and the resolved decisions, then stop.
Do not create implementation code, executable tests, package manifests, or install dependencies.
```

### Revising documents after the user's review

```text
I updated the USER sections. Reconcile all Stage 1 documents with my changes.
Preserve my wording and unrelated decisions. Update the resolved choices,
specifications, acceptance cases, and planned testing/generation instructions.
Report any actual conflict. Stop before writing code.
```

### Stage 2 instruction the user can send

```text
Read Instruction_for_Agent.md, AGENTS.md, and the current project specifications.
Execute Stage 2. First reconcile any edited USER inputs with the derived documents.
Implement the retained server, tests, and reusable generation harness.
Use the harness to generate both clients, build them, and run the required checks.
Verify clean regeneration without prior client source and without changing test assertions.
Update README, testing instructions, status, design decisions, and evaluation evidence.
Report actual results and blockers; do not invent successful runs or manual observations.
```

Stage 1 produces complete specifications using the effective preferences at that time, not a collection of empty headings. Blank preference cells remain blank in the source forms; their effective defaults are recorded separately. A user may directly request Stage 2 after reviewing the default-based documents. If a genuine contradiction prevents implementation, explain it and continue independent authorized work.

## 2. Project requirements and fixed project choices

The following is the project's requirements summary, not a verbatim external source. It is sufficient to begin the two-stage workflow without another attachment. Where an original requirements source is available, compare it using the provenance rules below.

### Deliverable and constraints

- The main deliverable is a reusable **code generator** that converts written specifications into working clients through **Codex or Claude Code**. A working messaging application alone is insufficient.
- If the generated client source is deleted, the documented generator must recreate working clients whose behavior matches the specifications. Regeneration is the primary evaluation criterion.
- The project requires two clients in different languages with independent messaging implementations. The selected project languages are **Python and TypeScript**. Shared protocol documents, schemas, fixtures, and test expectations are allowed; do not share a messaging implementation between the clients.
- Default interfaces are a Python command-line client and a TypeScript browser application. The user can revise their preferences through the designated source fields.
- Application runtime is local: localhost or an emulator is acceptable. No cloud messaging service, external runtime service, or turnkey messaging/chat SDK. General-purpose transport, JSON, storage, and UI libraries are allowed. Coding-tool authentication is a generation-time dependency, not an application runtime service.
- A small local server is sufficient: one process with in-memory state. Do not overbuild it. State loss on server restart must be explicit in the contract and demonstration instructions.
- Required messaging behavior: identify by username on first launch; send addressed text; queue locally during an outage and flush after reconnecting; display messages received from the server.
- Deliver one or more Git repositories as an archive containing real history. Commit generated client source and dependency declarations. Mark generation boundaries and actual authorship. Preserve authentic incremental work; do not fabricate a development history or attribute agent-written material to the user.
- Review considers design principles, agent setup, authorship clarity, real commit history, authoritative specifications, interoperability, regeneration, adaptability to evolving specifications, appropriate structure, and testing quality. FUTURE.md is optional in the source requirements and included in this project's workflow.
- Favor correct behavior and reproducibility over feature count or server complexity within the available engineering time.

### Required messaging scenario

Keep the same server process running throughout. Disconnect clients independently, allowing the other client and the server to continue operating.

| Step | Action | Required result |
|---|---|---|
| 1 | Alice sends Bob `Hi Bob, I have something important to tell you`. | Bob receives and displays the exact text. |
| 2 | Bob replies `What is it?`. | Alice receives and displays the exact reply. |
| 3 | Alice goes offline and queues a message. | Alice retains it locally pending transmission. |
| 4 | Bob goes offline and queues a message. | Bob retains his own local pending message. |
| 5 | Alice reconnects while Bob remains offline. | Alice's queued message reaches the server. |
| 6 | Alice goes offline again after server acceptance. | The shared server remains running. |
| 7 | Bob reconnects. | Bob receives Alice's queued text and submits his own pending text. The relative order of these two observations is unspecified unless the final protocol constrains it. |
| 8 | Alice reconnects once more. | Alice receives Bob's queued text. This extra verification supplements the source requirements' original seven steps. |

Stage 1 must choose explicit fixture text for the two queued messages and precise observable criteria. Do not replace the quoted texts in steps 1 and 2. Use external per-client network/proxy faults to test actual transport failures; keep static browser assets reachable when testing reload persistence.

An original requirements source may be inside the project or at an explicitly supplied external path, including a parent directory. If accessible, read it as the authoritative reference for its requirements and keep the original unmodified. Author `docs/ASSIGNMENT.md` as a neutral **Project requirements summary verified against the supplied source** only after comparison. Record a neutral source identifier, a content hash when available, comparison status, and any differences. The existing `ASSIGNMENT` filenames identify traceability documents; their contents and public descriptions use standalone requirements and review language.

By default, an external original remains a reference outside the deliverable. Record `NOT_INCLUDED` when it is not copied into the repository; this does not mean it was unavailable or unverified. Do not copy the original verbatim, personal source paths, or commissioning details into committed documents without an explicit user request to include them. Reading a reference does not authorize publishing it.

If no original is accessible for the current run, derive `docs/ASSIGNMENT.md` from this section and label it **Project requirements summary derived from Instruction_for_Agent.md**. Record source availability and comparison separately: `UNAVAILABLE` for an inaccessible original and `NOT_COMPARED` for a comparison that has not occurred. Do not infer that a source was never supplied merely because it is outside the project directory. Never label a reconstruction as a verbatim original or claim comparison with an unavailable source. Report any conflict with an available original instead of silently rewriting its obligations.

## 3. Project structure and ownership

Create the required Markdown files during Stage 1. The implementation folders below describe Stage 2 destinations; do not populate them with code during Stage 1.

| Path | Role | Created/populated in |
|---|---|---|
| `Instruction_for_Agent.md` | This construction guide; maintain its single canonical copy | Already supplied |
| Root Markdown documents | User navigation, agent rules, design, generation, tests, and change requests | Stage 1 |
| `specs/` | Product intent, acceptance contract, shared protocol, and platform specifications | Stage 1 |
| `docs/` | Requirements provenance/summary, decisions, status, review evidence, and completed changes | Stage 1 |
| `generator/` | Reusable Python orchestration of the selected coding tool, targets, builds, and bounded repair | Stage 2; retained |
| `server/` | Small local Python messaging server | Stage 2; retained |
| `tests/` | Independent tests, reference fixtures, transport fault controls, and acceptance assertions | Stage 2; retained |
| `scripts/` | Setup, launch, test, regeneration verification, and packaging entry points | Stage 2; retained |
| `generated/python-client/` | Python client source and its target-specific dependency declarations | Stage 2; generated |
| `generated/typescript-web/` | TypeScript browser client source and its target-specific dependency declarations | Stage 2; generated |
| `artifacts/` | Actual reports and sanitized generation/build/test evidence, organized by run | Stage 2 |

Only the two directories under `generated/` are client deletion/regeneration boundaries. Retained components may also be agent-authored: **authorship and regeneration ownership are different facts**. Document both. Keep secrets and machine-specific authentication out of the repository and reports.

### Required Markdown documents

Author these 16 documents. The descriptions below are content contracts, not text to paste as unfinished templates.

| File | What Stage 1 must produce |
|---|---|
| `README.md` | Public code-generator guide: purpose, folder roles, user-edit map, two-stage instructions, planned setup/run/test/regenerate workflow, generation boundaries, change-request workflow, and honest current status. |
| `AGENTS.md` | Instruction to read this file; W01-W05 USER preferences; preservation rules; stage boundaries; testing/repair discipline; allowed generated outputs; change-request handling. |
| `DESIGN.md` | D01-D05 USER priorities; resolved architecture; design tradeoffs; reliability limits; dependency rationale; actual authorship/provenance. |
| `GENERATE.md` | Complete harness input/output/configuration contract, tool/model readiness plan, target selection, isolated staging, integrity checks, bounded repair, validated publication/rollback, and clean-regeneration procedure. Planned commands must be clearly labeled. |
| `TESTING.md` | Planned setup and automated tests, the exact manual scenario with expected observations, restart/failure checks, evidence requirements, and blank M01-M06 observation fields. |
| `FUTURE.md` | Empty active request list, concise writing guidance with adjacent examples, review/apply instructions, and completion/removal rules. No prewritten feature requests. |
| `specs/PRODUCT.md` | P01-P11 USER preferences plus resolved, numbered requirements and explicit scope/limits. |
| `specs/ACCEPTANCE.md` | A01-A05 USER expectations, the required scenario, concrete fixtures, and executable-test specifications with expected observations and deadlines. |
| `specs/PROTOCOL.md` | Complete shared API and synchronization contract, including schemas, identifiers, validation, ordering, persistence boundaries, errors, and failure/recovery behavior. |
| `specs/PYTHON.md` | Complete Python CLI, storage, concurrency/lifecycle, transport, testing-interface, dependency, and launch contract. |
| `specs/TYPESCRIPT.md` | Complete browser UI, storage, concurrency/lifecycle, transport, origin/static-asset, build, and testing contract. |
| `docs/ASSIGNMENT.md` | Neutral requirements summary with source availability, inclusion, comparison status, and limitations as specified in Section 2. |
| `docs/ASSIGNMENT_REVIEW.md` | Criterion-by-criterion mapping to requirements, planned implementation, checks, and actual evidence status. Distinguish documentary coverage from demonstrated compliance. |
| `docs/DECISIONS.md` | Effective preferences and derived decisions, each with source, provenance, rationale, affected requirements, and any conflict. |
| `docs/STATUS.md` | Separate documentation readiness, environment readiness, implementation completion, automated/evolution evidence, manual review, and release readiness. Planned work must not appear as passed. |
| `docs/CHANGES.md` | Empty completed-change history and a definition of the evidence required for future completed entries. |

If Claude Code is selected, also create a short root `CLAUDE.md` directing it to read `AGENTS.md`, this file, and the current specs. Keep preferences in one place; do not duplicate them in that bridge.

On an existing project, read the current documents first. Preserve user-authored text and valid completed contracts, update affected agent-owned sections, and create missing documents. Do not reset inputs or erase implementation evidence by treating every run as a new project. Do not create missing documents from nonexistent attachments or assume a separate template pack exists.

## 4. User input forms and ownership rules

Create the following USER sections in the corresponding generated documents. The user edits the generated forms, not this field catalog or a duplicate README settings table.

| Document | Section key | Field IDs | User contribution |
|---|---|---|---|
| `specs/PRODUCT.md` | `PRODUCT_CHOICES` | P01-P11 | Product intent and user-visible behavior |
| `specs/ACCEPTANCE.md` | `ACCEPTANCE_CHOICES` | A01-A05 | Scenarios and expected outcomes |
| `DESIGN.md` | `DESIGN_CHOICES` | D01-D05 | Priorities, constraints, and tradeoffs |
| `AGENTS.md` | `WORKFLOW_CHOICES` | W01-W05 | Coding-tool and working preferences |
| `TESTING.md` | `MANUAL_OBSERVATIONS` | M01-M06 | Facts from actual manual execution |

For each section key, create paired HTML comment markers in the form `<!-- USER:BEGIN KEY -->` and `<!-- USER:END KEY -->`. Put its editable table between the markers.

Preference tables have columns `ID`, `Question`, `Your input`, and `Example / automatic default`. Observation tables have columns `ID`, `Observation`, `Your observation`, and `Example / behavior if blank`. Keep examples directly beside the corresponding input cell. Preserve the IDs and meanings defined below. Do not add a mandatory questionnaire for routine technical choices.

- There are 26 optional preference fields and six observation fields. The agent creates all forms. The user supplies personal intent, preferences, and actual observations; the agent writes the technical contracts.
- Initially leave input cells blank unless they already contain user-authored values. The catalog below defines defaults, not claims that the user personally supplied every requirement.
- Blank/whitespace-only preference cells, `TBD`, and `—` select their adjacent defaults. Treat `false`, `0`, and `none` as explicit values and validate compatibility.
- Record effective values in `docs/DECISIONS.md` with provenance `USER_EXPLICIT`, `TEMPLATE_DEFAULT` (the example/default catalog), or `AGENT_DERIVED`. Do not fill the user's cells with defaults on their behalf.
- Missing facts are not preferences. Preserve `NOT_RUN`, `NOT_RECORDED`, `UNVERIFIED`, or `BLOCKED` as appropriate; never turn an observation example into evidence.
- Preserve USER sections on revisions. An explicit selected change request may authorize the minimum necessary change to an affected source decision; archive its original wording and preserve unrelated inputs.
- Ask only about an actual conflict or necessary user-only fact that cannot be resolved from the authorized defaults and context. Never assume credentials, account entitlement, installed versions, or test success.

The following compact catalogs define which fields to create. They are not complete Markdown file examples.

### Product choices — `specs/PRODUCT.md`

| ID | Field to create | Adjacent example / automatic default |
|---|---|---|
| P01 | What is the project called? | `reusable-spec-driven-code-generator` |
| P02 | What should the project demonstrate? | A reusable generator can recreate independent Python and TypeScript messaging clients from a precise specification. |
| P03 | Who will use or review it? | A developer or reviewer running a small local demonstration on one computer. |
| P04 | What interfaces should the two clients have? | Python command-line client and TypeScript desktop-browser client. |
| P05 | What should the browser screen contain? | Username entry, recipient field, message input, Send button, inbox, outgoing-message list, and clear connection/status feedback. |
| P06 | How should identity work? | Enter a username on first launch and remember it across normal restarts; use an explicit reset to change identity. No password. |
| P07 | What must survive a client restart? | Username, queued messages with their original IDs, received messages, and synchronization progress. |
| P08 | Which offline experience is required? | A running CLI or already-loaded page can queue messages while the API is unreachable; offline first load/reload of browser assets is excluded. |
| P09 | What send feedback should users see? | `queued`, `accepted by server`, or `failed`, with an actionable error; server acceptance is not a read/delivery receipt. |
| P10 | What additional feature is essential? | None beyond the project's required messaging behavior. |
| P11 | What is intentionally out of scope? | Attachments, groups, reactions, passwords, cloud deployment, push notifications, closed-app delivery, and read receipts. |

### Acceptance expectations — `specs/ACCEPTANCE.md`

| ID | Field to create | Adjacent example / automatic default |
|---|---|---|
| A01 | Which restart scenario matters most? | Given a queued message, when I restart that client with the same store and reconnect, its original text is delivered once. Browser assets remain reachable during reload. |
| A02 | What repeated-send failure should be checked? | Given the server accepts a message but its reply is lost, when the client retries, the recipient still sees one inbox entry. |
| A03 | What should happen to invalid input? | Empty messages and invalid recipients show a clear error; valid Unicode, spaces, and newlines are preserved exactly. |
| A04 | What manual usability check matters? | I can distinguish queued from accepted messages and find the sender and exact text of each incoming message without reading logs. |
| A05 | What extra acceptance case do you want? | None beyond the fixed scenario, A01–A04, and the technical boundary tests derived by the agent. |

### Design priorities — `DESIGN.md`

| ID | Field to create | Adjacent example / automatic default |
|---|---|---|
| D01 | What is the priority order? | Correct offline behavior, clean regeneration, readable specifications, implementation simplicity, then visual polish. |
| D02 | How much server complexity is acceptable? | One local Python process with in-memory state; no server database or authentication service. |
| D03 | What dependency policy should guide the agent? | Prefer standard libraries and small general-purpose tools; no turnkey messaging SDK and no runtime CDN. |
| D04 | What reliability limitation is acceptable? | Delivery guarantees apply within one continuously running server session; restart the demo with explicit fresh client stores after server restart. |
| D05 | What tradeoff should resolve routine design choices? | Prefer a small understandable solution over a reusable abstraction unless the abstraction is necessary for the code-generation harness. |

### Working preferences — `AGENTS.md`

| ID | Field to create | Adjacent example / automatic default |
|---|---|---|
| W01 | Which coding tool should the harness invoke? | Codex; Claude Code is the other permitted choice. |
| W02 | How should a generation model be selected? | Use a model actually available to the same authenticated CLI/account as the harness; verify one noninteractive request. Record the tool version, requested model, and effective model when reported; otherwise record the effective model as `UNREPORTED`. No hard-coded model is assumed to work. |
| W03 | How should routine technical decisions be handled? | Choose a minimal compatible implementation, record the rationale, and continue; ask only when explicit requirements conflict or necessary user-only information is missing. |
| W04 | What are the repair and test limits? | Up to 3 client repair attempts after initial generation; 30 seconds per observable messaging transition, with separate bounded build and tool timeouts. |
| W05 | How should progress be reported? | Brief updates at meaningful milestones, with actual results, blockers, and next steps. |

### Manual observations — `TESTING.md`

| ID | Observation field to create | Adjacent example / behavior if blank |
|---|---|---|
| M01 | Actual test environment | Example: Windows 11, browser and version copied from its About page. Blank: `NOT_RECORDED`. |
| M02 | Actual test time and implementation revision | Example: local date/time and Git commit hash from this run. Blank: `NOT_RECORDED`. |
| M03 | Required offline scenario result | Example after verification: PASS; both queued texts appeared once after the specified reconnections. Blank: `NOT_RUN`. |
| M04 | Restart-persistence result | Example after verification: FAIL; queued text disappeared after the browser reloaded. Blank: `NOT_RUN`. |
| M05 | Usability observations | Example after verification: I could not distinguish queued from accepted because the labels looked identical. Blank: `NOT_RECORDED`. |
| M06 | Evidence location or reproducible steps | Example: a test report path plus the exact action sequence that reproduced the failure. Blank: `NOT_RECORDED`. |

## 5. Technical specification quality

Stage 1 must turn the effective requirements into a complete, internally consistent contract. The agent selects routine technical details and records why they fit the requirements. Do not leave routes, storage behavior, error handling, or required acceptance criteria as unspecified implementation choices.

### Shared behavior and protocol

Specify exact transport endpoints or message types; request/response/event schemas; field types and limits; username normalization; exact text preservation; identifier generation and collision handling; error codes; and compatibility/versioning assumptions. Define browser-origin handling and connection configuration. Distinguish application errors from temporary transport failure.

Define local message states and transitions, the meaning of server acceptance, recipient retrieval, and any acknowledgment. State what is durable and when. Specify retry/backoff/timeouts, local FIFO ordering, server ordering/cursors, idempotency keys and conflict detection, persistent inbox deduplication, and recovery after a lost response or crash. Do not promise exactly-once network delivery; define the observable duplicate-prevention guarantee and its session/storage limits.

Cover messages to a recipient that has not launched yet, both clients disconnected simultaneously, restart with queued messages, acknowledgment loss after server acceptance, cursor advancement versus durable inbox writes, storage failures, and server-session resets. Specify how automatic synchronization runs while the interface remains usable. The server's in-memory limitation must agree with client recovery and manual-test instructions.

### Platform contracts

Keep common behavior in PRODUCT/PROTOCOL/ACCEPTANCE and language/runtime details in the platform files. For Python, specify commands, prompts, text entry/display, a persistent store, lifecycle/background work, graceful shutdown, and a way for retained tests to drive the real client. A machine-readable test interface must exercise the production client logic.

For TypeScript, specify the browser screen and interactions, persistent store, async scheduling, identity/reset behavior, reload and multi-tab policy, static assets/origins, build/launch contract, and observable UI states for browser tests. Under the default scope, an already-loaded page can queue during API failure; offline first load and closed-tab delivery are excluded. API-only fault tests must leave assets reachable when reloading.

Choose precise dependency and version constraints when available. Planned compatibility choices in Stage 1 are not evidence that the packages were installed or tested. Resolve and record actually tested versions during Stage 2. No runtime CDN or hidden external messaging dependency.

### Traceability and evolution

Use stable requirement and acceptance IDs. Map each case to its source requirement and record which platform differences are allowed. Resolve behavior questions from the written contract. Updating specifications must be sufficient to drive regenerated behavior; never depend on an undocumented manual edit to generated code.

After initial creation, current source forms, resolved decisions, and completed specs govern the project. Use this guide for process and required structure; do not reapply an old default to undo an explicitly authorized later change. If current files conflict, reconcile their documented intent and provenance before implementation.

In the initial baseline, document how target configuration and registered specification extensions support evolution. Record executed evolution evidence as `NOT_RUN` until a real change has been authorized and verified. A successful baseline regeneration proves the baseline can be reconstructed; it does not by itself demonstrate changed behavior from an evolved specification.

Demonstrate evolution through a user-selected change request under Section 7 or an explicitly requested isolated experiment under Section 9. Do not create a feature request on the user's behalf, populate the empty queue, or carry over a feature or experiment from a previous project. Deferred evolution evidence is a disclosed limitation, not an implicit new feature or a blocker to baseline Stage 2 implementation completion.

## 6. What the generated README must explain

Write README for a developer or reviewer using the code generator. Include:

1. The generator's purpose and the messaging example, current stage, and verified versus planned functionality.
2. Every folder's role, where to find the harness/specs/server/clients/tests/evidence, and the exact generated deletion boundaries.
3. A section named **What you can edit**, with the five USER-section keys, field ranges, what the user writes, and adjacent examples. Explain blank preference defaults and blank factual observation behavior. Identify agent-owned documents and technical sections.
4. The exact Stage 1, review/revision, Stage 2, and manual-testing sequence. Explain that Markdown does not execute itself and the user explicitly instructs the agent.
5. Prerequisites and setup, tool authentication, generation of all/individual targets, launch of both clients and the server, automated tests, the manual walkthrough, and clean regeneration. During Stage 1, commands are proposed interfaces and must be labeled **PLANNED — not implemented or verified**. During Stage 2, replace them with the actual supported commands and tested environment details.
6. Where the user sees messages and queued/accepted/error states, how to induce each client's API outage, how to reconnect, and how to verify outcomes. Link to TESTING.md rather than requiring the user to infer steps from source code.
7. A section named **How to request changes**, explaining FUTURE.md editing, review versus implementation, copy-ready agent instructions, verification, history archival, and removal of completed requests only.
8. Limitations, actual authorship, real test evidence, unresolved blockers, and final archive preparation including Git history and generated source. Distinguish completed Stage 2 implementation from pending user manual review and final release readiness. Never describe an unexecuted procedure as successful.

Do not make README a second preference form or a duplicate of this entire construction guide. Keep it useful as the repository's real entry point after implementation.

## 7. FUTURE.md and completed changes

Create FUTURE.md with an `Active requests` section between `<!-- CHANGE_REQUESTS:BEGIN -->` and `<!-- CHANGE_REQUESTS:END -->`. Its initial content is **No active requests yet.** Create docs/CHANGES.md with **No completed requests yet.**

Do not prepopulate requests, reserve request IDs, reconstruct earlier feature ideas, or promote instructional examples into tasks. The user will inspect the results and decide what to add. Keep the filename `FUTURE.md` consistent across documents.

Explain how to write a request: unique ID, desired change, expected result, affected scope, behavior to preserve, and optional reason/priority. Put a short example beside each user-written field. For example, a description could request searching locally stored messages; label such examples as instructional only. A nonempty desired change is required. An empty request never means “implement the example”; omitted optional detail can be derived from the actual request. IDs start at CHG-001 and must remain unique across the queue and completed history.

Include copy-ready instructions in README and FUTURE for both operations:

- **Review:** read active requests and propose clarifications, scope, order, and test impact without changing code or applying the requests.
- **Apply selected IDs:** update the affected source decisions, specs, tests, implementation, and operating docs; verify; archive the original request and evidence in docs/CHANGES.md; then remove only completed selected items from FUTURE.md.

Saving FUTURE.md does not start an agent or authorize its entire contents. A direct apply instruction authorizes necessary supporting edits; do not repeatedly ask permission for routine implementation choices. Unselected requests remain untouched.

For an applied code change, update authoritative specs first and retained tests for the deliberately changed contract. Keep these controlled edits separate from generator repair, which cannot modify retained tests/specs. Regenerate affected clients through the harness, run relevant checks and clean regeneration, and update the operating docs and provenance. Do not clear a request merely because its specification was edited.

Archive the request's original wording, any changed USER decision and its previous value, affected requirements/files, actual validation commands/results, and available revision evidence. Archive before removing the active entry; avoid duplicate records on retries. Keep failed, blocked, partial, or required-user-check items with an accurate state and reason. Preserve the queue file, unrelated requests, examples, and completed history. A documentation-only change needs appropriate document checks rather than application regeneration.

## 8. Stage 1 execution and completion gate

1. Read this guide, any available requirements source at a supplied project or external path, and existing project documents. Identify current user inputs and actual constraints. Do not depend on a separately supplied README, specs folder, or template pack.
2. Create the required Markdown documents from the content contracts. Add all USER forms and adjacent examples, preserving existing inputs. Leave the change queue and completed history empty on a new project.
3. Resolve the effective preferences and record provenance. Author complete shared and platform contracts, concrete acceptance cases, design rationale, and harness/test procedures. The agent chooses the technical detail; the user is not required to author wire protocols or database designs.
4. Review consistency across inputs, requirements, schemas, platform behavior, acceptance cases, generator boundaries, commands, and status. Check Markdown links, exact filenames/case, unique IDs, and the user-edit map. Map every source criterion to its documentary coverage and required future evidence. Identify any manual checks required for final user sign-off and distinguish optional checks and deferred evolution evidence.
5. Report created/updated documents, effective defaults, the exact fields the user can edit, and any real conflict. Record documentation readiness separately from implementation and execution. **Stop before code.**

Stage 1 is complete only when all required documents exist and all implementation-critical contracts are resolved. Empty technical headings or “the agent will decide later” placeholders do not satisfy it. Future execution evidence must remain explicitly unverified; that is not a missing technical specification. A conflict requiring user input stays visible and prevents claiming the affected contract is complete.

Do not create application code, generator scripts, executable tests, package manifests, installed dependencies, or fake execution reports during Stage 1. Schemas, payload examples, pseudocode, and planned commands inside the specifications are allowed when they clarify the contract.

## 9. Stage 2 implementation and generation

Before implementing, read current USER sections and reconcile any edits with derived specs. An explicit Stage 2 request authorizes this reconciliation and ordinary implementation. Preserve user wording and scope. Do not replace completed specs with initial defaults or import unselected FUTURE requests.

### Retained components and harness

- Implement the small server and independent retained tests from the agreed contract. Test expectations come from specs, not from reverse-engineering a generated client.
- Build a reusable harness driven by declared spec paths, target configuration, output paths, coding-tool configuration, and build/test commands. It must invoke the actual selected coding tool to produce clients, not copy checked-in client code or a hidden implementation template.
- Separate shared and target-specific context. Record generation inputs, actual tool/model versions, target, command, attempt, result, and sanitized evidence. The harness must work when client package manifests and source are initially absent and install/build each target after generation.
- Treat a parent harness's explicit target-generation request as authorization for that target only. It does not recursively start either construction stage or authorize changes to the harness, retained server/tests/specs, the other target, or repository history.
- Generate candidates in new isolated workspaces using an allowlisted input snapshot. Give each target only its registered requirements and workflow context; provide only its own candidate and relevant diagnostics during repair. Exclude previous client implementations, sibling-project source, Git objects, and old source-bearing transcripts from agent inputs. Combine clients only in the trusted verification workspace.
- Freeze the complete retained input inventory and content hashes before generation. Check them after every agent invocation and trusted validation step. Reject retained-file changes, additions, removals, unexpected output paths, and source symlinks or path traversal. Document narrowly scoped exceptions for disposable build/dependency outputs; they must not conceal retained-source changes or enter published source.
- Verify a successful authenticated noninteractive coding-tool request in the same environment/account used by the harness. Do not assume a documented model name is available. If access fails, continue independent server, tests, and harness work, but mark actual client generation and clean regeneration BLOCKED.
- Bound execution time and repair attempts according to the effective workflow choices. Surface real errors, give a nonzero failure result, and prevent the repair loop from modifying retained specs, tests, assertions, or server behavior to make a broken client pass.
- Build candidates and run their retained checks before publication. For both-target generation, require interoperability to pass before publishing either replacement. For one target, include the existing other client only in trusted verification when available; otherwise report interoperability `NOT_RUN` and limit any success claim to the selected target's checks.
- Preserve published clients until all checks required for the selected scope and integrity comparisons pass. Publish only allowlisted candidate source, dependency declarations, and lockfiles produced by actual package-manager commands into the selected boundaries. Support rollback if publication fails; leave unselected targets and unrelated files unchanged. Dependency caches, runtime stores, and build outputs are not committed client source.
- Behavioral fixes to generated clients must be reproducible from generation inputs and the harness, not solely manual patches. Record failed candidates and preserve their sanitized diagnostics without treating a failed or partial run as a successful replacement.

### Testing and manual verification

Automated tests must exercise actual client implementations and actual browser interactions where relevant. Cover the fixed scenario, reversed client roles, offline queues, ordering, restart persistence, lost acknowledgments, duplicate prevention, validation, text preservation, and selected storage/lifecycle boundaries. Use bounded observable waits instead of fixed sleeps as proof. Test transport failure independently of server shutdown.

Provide a reproducible local launch path, separate client identities/stores, exact outage/reconnect actions, reset instructions consistent with the server-session limit, and expected visible results. Include appropriate instructions for the user's actual environment rather than assuming shell commands work on every OS.

The user records M01-M06 after personally running the walkthrough. Automated test reports and agent observations are separate evidence; do not fill the user's manual log or mark a required manual check passed without actual user input.

### Authorized evolution verification

For a selected change request, follow Section 7. For a separately requested experiment, create an isolated workspace and leave the baseline release and FUTURE queue unchanged. Before generation, declare the specification delta, active extension inventory, independent acceptance changes, and any necessary retained-server support. These deliberate contract changes are outside the client repair loop.

Use the ordinary harness to generate the affected clients and run the unchanged baseline assertions where applicable plus the new or deliberately revised assertions for the changed contract. Record the exact intended test delta and freeze it across repairs. Compare hashes of generic orchestration and prompt templates before and after; a feature-specific change to those components means the experiment has not demonstrated adaptation through specification/configuration changes alone. Record actual commands, results, input/test fingerprints, and migration checks when persistent state changes. Mark the experiment incomplete if its required checks fail or cannot run. Do not invent a CHG entry for an experiment requested outside the queue.

### Clean regeneration and submission

Run clean regeneration in a disposable workspace. Retain specs, harness, server, tests, and necessary dependency/configuration inputs. Exclude previous generated source and indirect copies, old generation transcripts containing source, build outputs/caches, agent sessions, and Git history/objects that would expose it. Preserve the user's working tree.

Invoke the real harness to recreate both clients, build them, and rerun the same retained tests with unchanged assertions. Record the input/test revision or hashes and actual results. Behavioral equivalence is required, not byte-identical generated source. If a failure requires a legitimate contract change, document that change explicitly and begin a new verification run; never silently weaken the oracle within repair.

Update README with the commands actually used and their results. Update DESIGN, GENERATE, TESTING, DECISIONS, STATUS, and ASSIGNMENT_REVIEW where affected. Preserve authentic incremental Git history and generated source; include the history in the repository archive. Verify its source inventory and documented history-restoration procedure. An archive may be prepared for user review while manual checks are pending, provided its status and documentation say so. Record unavailable Git identity, tools, account access, or tests as specific blockers rather than manufacturing evidence.

## 10. Completion and evidence rules

| Evidence category | Honest Stage 1 state | What establishes completion later |
|---|---|---|
| Documentation | COMPLETE only after the Stage 1 consistency review | Current specs agree with user inputs and source requirements |
| Environment/tool access | UNVERIFIED unless actually checked | Recorded versions and successful authenticated harness-context request |
| Implementation | NOT_STARTED for a new Stage 1 project | Retained components and both generated clients exist and build |
| Automated acceptance | NOT_RUN | Actual passing reports for required scenarios and boundaries |
| Clean regeneration | NOT_RUN | Actual generation without previous client code, followed by the same passing tests |
| Evolution execution | NOT_RUN | An authorized specification change or experiment passes its declared checks; remains explicitly deferred until requested |
| Manual observations | NOT_RUN / NOT_RECORDED | The user's factual observations and evidence |
| Archive | NOT_CREATED | Committed source and real history are packaged; source inventory and history restoration are verified |
| Final release readiness | NOT_READY | Required automated checks, any authorized evolution checks, declared required manual checks, and archive verification are complete |

Stage 2 implementation is complete when the retained components and generated clients exist, actual generation/build/required automated checks and clean regeneration pass, and the operating documentation and provenance reflect those results. Any separately authorized implementation or evolution work must also satisfy its declared checks. Do not block baseline implementation completion merely because M01-M06 are still blank or no evolution experiment was requested; report manual review as pending and evolution execution as deferred. These states do not imply final user sign-off or full demonstrated coverage of every review criterion.

Final release readiness is separate. Until the required manual checks identified during Stage 1 have actual user evidence and archive verification passes, retain `NOT_READY` with the specific remaining work. Optional checks remain clearly labeled and do not become release blockers during execution. Preparing a review archive does not manufacture manual evidence or final approval.

Do not claim requirements compliance solely because these instructions or the generated documents mention every criterion. In docs/ASSIGNMENT_REVIEW.md, distinguish requirements covered on paper from behavior demonstrated through actual execution. Keep source-comparison limitations and deferred evolution evidence visible; an original absent from the archive may still have been available and compared.

When reporting either stage, state what changed, what was actually checked, what the user should do next, and any material blocker. The user should be able to start with this one file, receive complete editable documents in Stage 1, and use those documents to obtain reproducible code in Stage 2.
