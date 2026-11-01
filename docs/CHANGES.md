# Completed changes

Completed requests and their actual evidence are recorded below.

This is the completion history for actual requests from [FUTURE.md](../FUTURE.md), not a fabricated history of the initial build. Stage 1 creation and ordinary project milestones belong in [STATUS.md](STATUS.md) and real Git history. No CHG IDs are reserved or inferred from examples.

## Required evidence for a completed entry

Before removing an active selected request, append one record containing its unique ID, original wording, scope/expected result/preservation constraints, original and revised affected USER values, affected requirement/acceptance IDs and files, implementation outcome, actual validation commands and counts/results, and genuine revision/commit evidence when available. Include applicable clean-regeneration evidence for code changes, or appropriate document checks for documentation-only changes. Preserve limitations and required manual results separately from automated reports.

Record date/time with timezone for actual work; never backdate history or fabricate authorship/commit IDs. An uncommitted change can record a real base revision and fingerprints without pretending it was committed. Archive the original request before removing it from the queue. On retries, find an existing ID and reconcile its record rather than duplicating it. Failed, partial, blocked, or required-user-check-pending requests remain active until their declared completion criteria are satisfied. A separately authorized experiment outside the queue does not invent a completed CHG entry.

## CHG-001 — Python desktop GUI — COMPLETE

Completed 2026-11-01T07:32:17.504822-08:00 (America/Los_Angeles). Implementation and required automated/evolution checks passed. General user confirmation was subsequently received as recorded below; detailed M01–M06 observations remain unchanged. This entry archives the original request before its active entry is removed.

### Original request (verbatim)

```text
CHG-001: Replace the Python terminal interface with a desktop GUI
- State: PROPOSED
- Change: Make the Python client usable through a desktop graphical interface with a layout and interaction flow similar to the TypeScript browser client.
- Reason: Both clients should support the same messaging tasks through comparable graphical interfaces.
- Scope: Python client presentation and lifecycle, relevant product/platform specifications, GUI acceptance tests, and launch/testing documentation. Adjust shared interface guidance and the browser presentation only where needed for consistency.
- Priority: Normal.
```

### Decisions, scope, and preservation

| Decision | Previous source cell and effective value | Result |
|---|---|---|
| P04 | Blank; default Python command-line client and TypeScript desktop-browser client | Cell stays blank; CHG-001 explicitly selects Python Tkinter desktop GUI and the existing TypeScript browser client. Provenance USER_EXPLICIT is the request, not a fabricated form entry. |
| P08 | Blank; default a running CLI or already-loaded page can queue while the API is unreachable | Cell stays blank; the running Python client is now graphical. Offline queue semantics and browser asset limits are preserved. This interpretation is AGENT_DERIVED from CHG-001. |
| All other USER preferences and M01–M06 | Original values/wording, including all blank cells | Preserved byte-for-byte in their USER blocks. No manual observation was supplied by the agent. |

Normal Python launch opens a desktop GUI. Both interfaces provide identity, composition, inbox/outgoing messages, connection status, development transport and confirmed reset. Desktop selection exposes full multiline text. The generated Python GUI and headless --machine interface share their Python production core; Python and TypeScript messaging implementations remain independent. SQLite version 1 is preserved, including old identity, IDs, order, pending/accepted/failed rows, inbox and cursor. No migration or wire/server change was needed. Browser source remains unchanged in the published project.

Affected requirements: REQ-UI-01 and REQ-TEST-01 directly; REQ-ID-01, REQ-TEXT-01, REQ-PERSIST-01, REQ-FAILURE-01 and lifecycle/reset presentation are verified through GUI-01–GUI-06. REQ-GEN-01–03 are supported by actual generation/evolution/clean-proof evidence. Existing AT-01–AT-18 obligations remain; GUI coverage is additive. Existing 44 baseline test cases are retained, with 11 new desktop cases. Deep nonprinting-scalar/protocol cases still use the production machine interface. GUI tests operate actual widgets; they do not call backend messaging operations.

Specifications/decisions: specs/PRODUCT.md, specs/PYTHON.md, specs/ACCEPTANCE.md, docs/DECISIONS.md and DESIGN.md. Retained changes: tests/gui_driver.py, tests/browser/desktop.spec.js, tests/browser/fixtures.js, scripts/gui_support.py, setup/environment/verify/demo/regenerate_check scripts, and generator/targets.json (required gui.py/native dependency declaration). Operating/evidence documents: README.md, TESTING.md, GENERATE.md, AGENTS.md, docs/STATUS.md, docs/ASSIGNMENT.md, docs/ASSIGNMENT_REVIEW.md and docs/EVIDENCE.json. The entire generated/python-client boundary was regenerated through the harness; no behavioral patches were applied manually. No protocol extension is registered; the selected registered contracts were revised.

### Actual validation and revision evidence

| Command / observation | Actual result |
|---|---|
| python3 scripts/check_environment.py | PASS: Python 3.10.12, Tk 8.6.12, isolated Xvfb window, Chromium 141.0.7390.37 and build tools. Native packages were installed by the user after the first prerequisite checks identified missing Tk/Xvfb. |
| Focused pre-generation GUI-01 check through retained Playwright/GUI driver | Expected FAIL: the previous client had no gui.py; one collected failing test demonstrates the new oracle detects the missing feature. Evidence artifacts/changes/CHG-001/red-check.json. |
| python3 scripts/verify.py --suite harness | PASS, 9/9; run 20261101T142656748004Z. |
| python3 generator/run.py --target python | PASS, run 20261101T142801177696Z; Codex 0.166.0, requested gpt-6-astra, effective model UNREPORTED. Initial generation only, 55/55 acceptance cases, zero failures/skips/flaky cases, publication PASS. |
| Agent visual inspection using actual generated desktop controls | PASS: accepted greeting, received reply, queued message, exact multiline detail panes; artifacts/changes/CHG-001/desktop.png and preview.json. This is agent evidence, not user manual sign-off. |
| python3 scripts/regenerate_check.py | PASS, run 20261101T151017779910Z; fresh generation 20261101T151030542008Z, attempts {"python": 2, "typescript": 2}. Both clients recreated without old source/Git/transcripts; 55/55 tests inside the harness and 55/55 again in standalone verification; zero failures/skips/flaky cases. Original tree preserved. |
| Earlier failed proof 20261101T143710332729Z | Initial TypeScript duplicate status identifier was repaired with frozen inputs; the fresh clients then passed 55 harness tests, but standalone verification passed 54/55 after main.js returned ERR_EMPTY_RESPONSE. The failed proof remains FAIL. Twelve focused restart repetitions and 500 sequential HTTP probes did not reproduce that transport failure. |
| Retained corrections / published-client recheck | aeb2441 disables proxy upstream pooling, adds body-free asset diagnostics, and strengthens GUI-04 to require an actually held GET response. The revised published-client suite passed 55/55 in artifacts/changes/CHG-001/corrected-fixture-acceptance.json. No retry/skip/timeout increase was introduced. These controlled changes precede the new clean proof. |
| Current clean candidate repair history | The initial Python candidate changed a persisted outbox error field during intentional offline restart; the retained snapshot assertion failed. The candidate was repaired, with the same frozen inputs and assertions, before successful publication. Attempt counts above include repairs. |
| python3 scripts/package.py | PASS; run 20261101T153354714666Z at 80f49af, 63 source files, byte comparison, bundle restoration and git fsck. Packaging is rerun after final evidence commits; each manifest records the exact revision. |
| Document/input consistency | USER blocks preserved; selected queue markers restored; local Markdown links and configuration checked. Final evidence/status edits do not alter behavior or test assertions. |

Authentic revisions: baseline 2b2d2058739bcc8cf35840b621f3369507e6c2f2; d68e6fd records revised specifications and independent GUI tests before generation; cb2265c records the harness-generated Python client and passing acceptance evidence. The clean proof uses retained inputs from aeb24419579fcdc8ad7fe11288eaaa3caf9c431b; its full input/test fingerprints and result summaries are recorded in EVIDENCE.json. Retained correction revision aeb2441 is a deliberate new verification snapshot; assertions were frozen within each run. Later documentation/archive commits recorded completion. The subsequent user-requested squash below consolidates Git history; these revision IDs remain the actual pre-squash execution snapshots.

### Evolution integrity

The generic components have identical before/after SHA-256 fingerprints:

| Component | SHA-256 before and after |
|---|---|
| generator/core.py | `6325957e7155bcca374ff1e7f897b789b4d9255d638da8b40e0b85c8a40cda43` |
| generator/run.py | `990d2723dea67df4856ed6e0add20369bdab262c6ceba482c0b509fea0e576f8` |
| generator/prompts/client.md | `1b3b0e66c959bb39c6926f8884e5958af49b29dc9318c055eb2bbbf5818c8d36` |

Server, PROTOCOL.md and published TypeScript source fingerprints also remain equal. Only declared contracts/configuration and supporting retained GUI tests/setup changed; no GUI-specific logic was added to generic orchestration or its prompt. Clean regeneration freezes the revised inventory across all generation/repair/check steps.

### Remaining limits

Ubuntu/WSL with Python 3.10 and Tcl/Tk 8.6 is the tested desktop environment. README and TESTING list `sudo apt-get install -y python3-tk xvfb x11-xkb-utils x11-utils`; a working desktop display is needed for manual GUI use, while automation uses an isolated Xvfb display. Native Windows/macOS are unverified. The server remains memory-only, and a new server session requires explicit fresh/reset stores. Optional OF-01/OF-02 crash/write-failure injection remains NOT_RUN. The user subsequently confirmed that the code works well, but detailed M01–M06 observations are still unrecorded; these do not invalidate the completed automated implementation/evolution checks.

### User confirmation and history consolidation — 2026-11-01

The user stated: “I confirmed that it works well.” This is general confirmation of the working code, not a claim that every documented manual scenario was individually reported. The source observation cells remain unchanged. README now contains only a concise change summary and a link to this detailed history.

At the user's explicit request, these five commits were combined with the README summary and confirmation record into one CHG-001 commit on top of `2b2d2058739bcc8cf35840b621f3369507e6c2f2`:

- `d68e6fd` — specifications and retained GUI tests.
- `cb2265c` — harness-generated desktop client and acceptance evidence.
- `aeb2441` — retained proxy corrections and delayed-response assertions.
- `80f49af` — completion and clean-regeneration evidence.
- `1e59986` — verified review archive evidence.

The original history is preserved in `artifacts/history/CHG-001-before-squash.bundle`, verified with `git bundle verify` before consolidation. This is a local backup excluded from source publication. Historical hashes above and in EVIDENCE.json continue to identify the original tested snapshots; they are not hashes of the consolidated commit. Earlier project history is preserved. No remote push is part of this consolidation. Existing archive verification remains evidence for its original revision, not the newly consolidated revision.

Consolidation checks: documentation whitespace validation, unchanged application/specification/test trees, preserved USER blocks, and a single commit after the unchanged baseline. Runtime checks were not rerun for this documentation/history-only operation.

## CHG-002 — Local server desktop GUI — COMPLETE

Completed 2026-11-01T13:08:15.988378-08:00 (America/Los_Angeles). Required automated checks and clean regeneration passed. The user subsequently confirmed that CHG-002 works well, as recorded below; detailed scenario observations remain unrecorded. This record is written before removing the selected request from FUTURE.md.

### Original request (verbatim)

```text
CHG-002: Add a desktop GUI for the local Python server
- State: PROPOSED
- Change: Add a local desktop GUI for starting, stopping, and monitoring the existing Python messaging server.
- Reason: The user should be able to operate the server and inspect its status and message activity without interacting with a terminal.
- Scope: The retained server, its management interface and lifecycle, relevant specifications, server/GUI integration tests, and launch/testing documentation.
- Dependency: An implemented baseline server and clients. CHG-001 is not required; validate with the current clients, including the Python GUI if it has already been applied.
- Priority: Normal. Suggested after CHG-001.
```

### Decisions, scope, and compatibility

The retained server now has an optional Tkinter/ttk control window (`python3 server/gui.py`) with Start, Stop, Open browser, session/address/status, response/error counts, recent responses, accepted messages, and exact selected-message text. The original terminal server remains available and uses the same Server/Handler. Listening stays loopback-only. Background startup/shutdown, tracked connection closure, and Tk-thread-only widget updates keep lifecycle actions responsive. Counts and the latest-200 displays are locked, bounded snapshots and do not consume messages or alter protocol state.

P10 remains blank (previous effective default: no extra essential feature); the later explicit CHG-002 adds server management. D02 remains blank with its small local in-memory-process default; the GUI uses the same process with one running Server per Start/Stop session. P04/P08 retain the CHG-001 client choices. All 26 preferences and M01–M06 USER blocks are unchanged. REQ-SESSION-01 clarifies that every new Server instance starts empty, including a GUI restart inside the same process. Fresh/reset client stores are still required. This is compatible with the local-runtime/small-server requirements and adds no cloud service, wire endpoint, database migration, or client behavior change.

Contracts were updated before implementation: REQ-SERVER-UI-01, specs/SERVER.md, PRODUCT/ACCEPTANCE, DESIGN and DECISIONS. Independent SG-01–SG-06 tests were written first and initially failed because server.gui was absent. Retained changes are server/gui.py, server/main.py, tests/server_gui/, tests/server_gui_driver.py, tests/browser/server-desktop.spec.js, tests/browser/fixtures.js and scripts/verify.py. README, TESTING and GENERATE document actual operations. No generated client was hand-patched or replaced; no targeted client regeneration was needed for this server-only delta. The actual clean proof nevertheless recreated both clients through the unchanged harness and ran the expanded suite.

### Actual checks and evidence

| Command / observation | Result |
|---|---|
| Pre-implementation retained test import | Expected FAIL: server.gui absent; artifacts/changes/CHG-002/red.json. |
| Initial native test attempt | Sandbox Xvfb socket denial, zero tests; not accepted as a pass. Authorized native execution then ran the tests. |
| First native GUI run | 7/8; production-window discovery matched the fixture window. Test fixture title corrected without weakening visibility checks. Pending Tk timer cleanup and closed-socket response handling were also corrected. |
| First expanded suite | 64/65; all application assertions passed, but SG-06 cleanup waited for a second exit from an already-signaled subprocess. Retained stop helper now recognizes signalCode. This failed report remains FAIL. |
| Focused server/client recheck | 2/2 PASS after the fixture correction; artifacts/changes/CHG-002/focused-restart.json. |
| python3 scripts/verify.py --suite all --report artifacts/changes/CHG-002/acceptance.json | PASS 65/65: 55 preserved cases + eight server-widget/HTTP tests + two GUI-managed client cases; zero failures/skips/flaky cases. |
| python3 scripts/verify.py --suite harness --report artifacts/changes/CHG-002/harness.json | PASS 9/9. |
| python3 scripts/regenerate_check.py | PASS 20261101T204250502871Z; actual all-client generation 20261101T204302588941Z, calls per target {"python": 3, "typescript": 3}. 65/65 inside the harness and 65/65 standalone, zero failures/skips/flaky cases; original tree preserved. |
| Clean-generation repair | Initial Python candidate changed a queued row error field during intentional offline restart; unchanged AT-01/AT-09 snapshot assertion failed. The next candidate passed 63/65 but failed two existing GUI-04 reset assertions (stale outbox and prematurely visible login). All new server GUI checks passed. Further ordinary bounded repair used the same frozen contracts/tests before the successful results above. |
| Agent visual inspection | PASS: actual control window, accepted messages/counts, and full Unicode/multiline detail; artifacts/changes/CHG-002/server-desktop.png. Not user manual evidence. |
| Document/source checks | USER blocks, published client hashes, protocol, generic generator/config/prompt preserved; local links and whitespace checked. Final documentation/evidence edits do not change the verified code, specs or tests. |

The verification snapshot was based on `d6fdcd50c850a9e9e1445de784f329eed2c07813` plus the authorized CHG-002 working-tree changes. Exact frozen inputs, call counts, output hashes and reports are recorded in EVIDENCE.json. Original generated source is identical to the pre-change snapshot; fresh generated source exists only in the disposable proof workspace. The generic runner, prompt and target configuration hashes are unchanged. Historical pre-squash revision IDs remain historical evidence, not newly invented commits.

### Manual verification and limits

Follow [the server GUI walkthrough](../TESTING.md#server-gui-manual-verification-chg-002): launch, Start, exchange messages with the current Python desktop/browser clients, inspect activity, Stop, then restart with fresh stores. README contains only a brief change summary. Native packages are unchanged: python3-tk, xvfb, x11-xkb-utils and x11-utils. Tests use isolated Xvfb; interactive use requires a working desktop display. The external browser-launch call is tested with a mock opener; actual browser launch on the user's desktop still needs manual confirmation. Native Windows/macOS remain unverified. Session monitoring is local/in-memory; no delivery/read receipt or online-user count is claimed. A new release archive must identify its own committed revision; old package verification does not establish the new archive.

### User confirmation — 2026-11-01

The user stated: “I found it works well.” This records general confirmation of CHG-002 after trying the application. Individual test results, environment details, and browser-launch observations were not specified, so M01–M06 remain unchanged. The confirmation and concise README status are included in the single local CHG-002 commit at the user’s request to commit and established preference for one commit per change. No application code or test assertions changed.
