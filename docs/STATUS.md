# Project status and evidence

Updated 2026-11-01 (America/Los_Angeles). The agent authored specifications and retained infrastructure/tests; actual isolated Codex harness calls authored both clients. Blank USER preferences are not user-authored answers, and automated/agent checks do not fill manual observations.

## P01 reconciliation and client regeneration

State: COMPLETE. Both generated client directories were initially absent and were recreated through the actual harness. P01 changes from blank/effective `reusable-spec-driven-code-generator` to explicit `Jaehyeok-spec-driven-code-generator`; its adjacent default and documentation are synchronized. The other 25 preferences remain blank. All six manual observations were blank and preserved during generation; subsequent user entries are recorded below.

This changes documentation identity only; existing CHG-004 messaging, GUI titles/selectors, paths and storage contracts are preserved. Retained tests/server, generic runner/prompt and target configuration are unchanged. FUTURE requests were not applied or supplied to candidate agents. No prior implementation or Git history was supplied to generation.

| Current check | Actual result |
|---|---|
| Input/default reconciliation | P01 source wording preserved; previous/new input and default recorded in DECISIONS; other USER values/observations preserved. |
| Setup/readiness | PASS after approved parent execution allowed Xvfb local Unix sockets; Tk 8.6.12, Chromium 141.0.7390.37, Node 22.17.0. Authenticated model preflight passed in both generation runs. |
| Harness guard checks | PASS 9/9; artifacts/reconciliation/20261102T002611038268Z/harness.json. |
| Published generation `20261102T002927228257Z` | PASS 92/92 before publication; three calls per target (initial plus two repairs). |
| Published setup/build/verification | PASS; 92/92 with zero failed/skipped/flaky cases; artifacts/reconciliation/20261102T002611038268Z/published-acceptance.json. |
| Clean proof `20261102T010021541172Z` | PASS 92/92 inside the harness and 92/92 standalone; original retained/generated tree preserved. Inner run `20261102T010033133984Z` used one initial call per target, no repair. |
| Integrity | Frozen input hashes and generated source inventories recorded in EVIDENCE.json; no manual generated-source patches or retained assertion changes. |

Published generation first failed the TypeScript build because a helper named status conflicted with a browser global. After that repair, acceptance passed 91/92: the existing web AT-13 timeout case did not display Offline. All new presence/layout cases passed. A second bounded repair fixed the browser candidate; the full suite then passed, including independent published-checkout verification. Both failures remain in actual reports; no assertion, timeout or retry policy was weakened. The clean proof passed on its initial candidate pair.

Requested model: gpt-6-astra; effective model: UNREPORTED; tool: codex-cli 0.166.0. Input revision: `050aa0f` plus recorded P01 reconciliation; final evidence documentation follows verification. Fresh proof outputs remain in the disposable workspace. Regeneration created no CHG entry; the user subsequently requested a commit. Current packaging and remaining manual evidence details are separate from the completed checks.

The user's subsequent TESTING.md entries report M03/M04 PASS and M05 Good, with Windows 11 mentioned in M01 and test time `11/1/2026, 9:20pm` in M02. All source wording is preserved. An actual browser/version, tested revision and M06 evidence were not provided; no agent observation fills those gaps. The user's observation edits and status reconciliation do not change generated code or the recorded runtime results.

## Current documentation baseline

The current specifications and preference examples describe completed CHG-001–004, including the Python/server GUIs, compact web layout, directory/durable receipts and explicit presence. Regeneration checks changed USER choices and reconciles them before freezing inputs; pending FUTURE requests remain excluded. At that documentation reconciliation, all 26 user inputs and six manual observations were blank and preserved. The later P01 update is recorded above; previous defaults and provenance remain in DECISIONS.

This documentation-only reconciliation consolidates existing behavior, route/scheduler rules and acceptance mappings. It changes no implementation, retained test assertion, generic prompt or target configuration. The runtime PASS results below remain evidence for their recorded snapshots; no application tests or model generation were rerun for these documentation edits. Documentation checks passed: 21 Markdown documents reviewed, 138 local links/anchors valid, USER input/observation preservation, archived CHG-entry preservation, and documented configuration matching targets.json. The generic prompt remains unchanged; the other 20 Markdown documents were synchronized.

## CHG-004 complete

Both clients explicitly notify the server when their Development transport changes, and the web interface follows the Python desktop layout. Server Offline state is independent of peer message traffic and cannot be undone by a late legacy heartbeat. Real connection loss still uses heartbeat expiry. Published generation 20261101T230328364307Z passed 92/92; one initial call per target. Nine harness guards pass. Clean proof 20261101T232007378344Z passed 92/92 inside the harness and 92/92 standalone and preserved the original tree; three calls per target (initial plus two repairs).

The first run was intentionally stopped after a compiler repair and a 90/92 result: Python reset exposed stale rows, and an isolated probe proved Chromium automatically retried the lost-reply fixture. The corrected fixture withholds the accepted reply until the client deadline. All acceptance assertions remained unchanged; a new generation run used fresh candidates. Clean generation separately repaired a TypeScript DOM-name conflict and a 91/92 run where an existing browser send-timeout check failed to show Offline. All new CHG-004 cases passed that run. Exact hashes and reports are recorded in EVIDENCE.json. USER blocks and generic generator/prompt remain unchanged. User manual review and a current release archive remain pending.

## Server presence display follow-up (historical)

The Users table now displays Online/Offline with a visible 15-second heartbeat explanation. Focused server GUI verification passed 12/12, including automatic expiry and recovery. This is a retained server presentation change; clients and wire behavior are unchanged. Full-suite and clean-regeneration results below describe the preceding CHG-003 baseline, not a rerun of this follow-up. See TESTING for manual checks.

## CHG-003 complete

Both generated clients and the retained server implement shared recipient discovery, click-to-address and per-user message activity. Queue semantics follow the explicit user clarification: server-accepted messages awaiting recipient acknowledgment are queued; offline client queues are unknown. Generation 20261101T213828695226Z passed 80/80 and published both clients after one bounded repair. Its initial 79/80 failure caught an existing Python reset regression and remains recorded. All new cases passed on that initial attempt. Nine harness guards pass.

Clean proof 20261101T215733141945Z regenerated both clients without prior source, passed 80/80 inside the harness and 80/80 standalone, and preserved the original tree. Each target used two calls (initial plus one repair); the initial clean candidate also passed 79/80 and failed the existing Python reset-display check. The generic generator core/runner/prompt and USER blocks are unchanged. The original request and evidence were archived in CHANGES before removal from FUTURE. Agent visual inspection of the server Users view and both client directory screens passed; user review of CHG-003 and a current archive remain pending.

## CHG-002 complete

The retained server desktop passes 65/65 acceptance cases and nine harness guards. Clean proof 20261101T204250502871Z recreated both clients with the unchanged harness, passed 65/65 inside it and 65/65 standalone, and preserved the original tree. Published clients, wire protocol, target configuration and generic runner/prompt remain unchanged. The request and evidence were archived in CHANGES before removal from FUTURE. The user confirmed CHG-002 works well on 2026-11-01; detailed scenario observations remain unrecorded.

The first full run passed 64/65 and timed out during SG-06 teardown; all its messaging assertions had passed. The fixture now recognizes already-signaled child processes instead of waiting for a second exit. The focused cases and corrected full suite pass. Earlier native checks exposed a fixture window-title collision and Tk/socket cleanup issues, corrected before the final snapshot. Failed reports remain recorded, without automatic whole-test retries, skips, deadline increases or weakened assertions. Agent visual inspection passed and is separate from user evidence.

## CHG-001 complete

The Python desktop client was generated through the actual harness and passed 55 acceptance tests; nine harness guards also pass. Independent GUI checks cover both-role messaging, exact text, legacy stores, restart, actual held-response reset, validation, responsiveness and shutdown. Agent visual inspection passed; user observations remain separate. Clean proof 20261101T151017779910Z recreated both clients and passed 55 tests inside the harness and again standalone while preserving the original tree. The original request and actual evidence were archived in [CHANGES](CHANGES.md) before removing its completed active entry.

Earlier clean proof 20261101T143710332729Z remains FAIL: TypeScript's initial compilation conflict was repaired, but standalone browser startup lost main.js with ERR_EMPTY_RESPONSE (54/55). Twelve focused diagnostic repetitions and 500 HTTP probes did not reproduce the transport failure. Retained correction aeb2441 disables upstream pooling for the closing server, adds body-free asset diagnostics, and makes GUI-04 assert an actual held GET response. No retry, skip, relaxed assertion, or increased deadline was used to turn the failure into success. Revised published-client acceptance and the new clean proof pass.

## Completion states

| Area | State | Evidence / remaining work |
|---|---|---|
| Stage 1 documentation | COMPLETE | All 16 required documents, source comparison, catalog forms, and contracts completed; current docs reconciled with implementation |
| Preferences | RECONCILED | P01=Jaehyeok-spec-driven-code-generator; 25 other inputs blank; prior/new default and explicit provenance recorded; no choice conflict |
| Environment | VERIFIED for this environment | Ubuntu 22.04.5/WSL2 x86_64; Python 3.10.12, SQLite 3.37.2, Node 22.17.0, npm 10.9.2, Git 2.34.1; Tk 8.6.12; native GUI prerequisites installed by the user |
| Coding-tool access | PASS | Project-local Codex 0.166.0, requested gpt-6-astra, effective UNREPORTED; authenticated writable preflight and real generation calls |
| Implementation | COMPLETE — clients regenerated | Both deleted client directories recreated and published only after 92/92 harness acceptance; published build/acceptance and independent clean proof pass. |
| Automated baseline | PASS | Current published verification: 92/92, zero failed/skipped/flaky; 15 protocol, four machine-interface, 13 server-GUI and 60 browser/client cases. |
| Harness guards | PASS | Current run passed all nine AT-18 guards; actual report retained under artifacts/reconciliation/20261102T002611038268Z/. |
| Clean regeneration | PASS | Current proof `20261102T010021541172Z` passed 92/92 inside the harness and standalone, preserving original source. |
| Evolution | PASS — CHG-001–004 | Client/server desktop, directory/durable receipts, explicit presence and compact browser layout verified; generic runner/prompt unchanged; stores remain version 1 |
| Optional storage/crash injections | NOT_RUN — deferred | OF-01/OF-02 remain disclosed optional executions; normal restart, malformed-page rollback, and unsupported-store checks pass |
| User manual review | USER-REPORTED PASS — offline and restart checks | M03/M04 PASS; M05 Good; M01/M02 supplied verbatim in TESTING.md. Actual browser/version, tested revision and M06 evidence remain unspecified. Earlier CHG-001/002 confirmations are preserved. |
| Review archive | PRIOR REVISION VERIFIED; CURRENT NOT_CREATED | Earlier archive/history checks remain historical. The newly generated P01 revision requires its own committed release archive. |
| Final release readiness | NOT_READY — remaining manual details and current archive pending | Current regeneration/automated checks pass, and user-reported offline/restart checks pass. Browser/version, tested revision, M06 evidence and current packaging remain outstanding. |

Baseline Stage 2 implementation completion requires generation, builds, required acceptance/guard checks, clean regeneration, and truthful operating documentation. Pending user observations and unrequested evolution remain separate; neither is silently marked passed.

## Actual execution history

[EVIDENCE.json](EVIDENCE.json) records run IDs, times, base revisions, input/source hashes, model/tool identity, rounds, and test counts without private workspace paths or raw transcripts. Detailed disposable logs remain under artifacts/.

| Run / check | Actual result |
|---|---|
| Global CLI readiness | Version 0.142.5 default gpt-5.5 was rejected with model_not_found. The parent sandbox initially denied local CLI state writes. |
| Project-local readiness | Version 0.166.0 + gpt-6-astra completed and wrote the probe file using the existing account. Approved execution allowed normal CLI state access; the child workspace sandbox and enterprise rules remained enabled. |
| Initial generation 20261101T130316383532Z | Both targets generated on their initial calls; build/interface/interoperability checks passed: 42 tests. Published source was then committed with genuine provenance. |
| Focused maximum-page regression | A valid 100-message escaped page measured 2,468,923 bytes. The initial Python client rejected it at its 2 MiB cap; the new retained regression failed for Python and passed for the browser. |
| Targeted generation 20261101T131743010141Z | Python recreated from the clarified contract without previous Python source, on the initial call. Expanded 44-test suite passed before replacement; browser source was preserved. |
| Harness guard verification 20261101T132713600115Z | Nine tests passed after final report/input-allowlist strengthening. |
| Clean proof 20261101T133420994052Z | Fresh inputs at c138989, no previous clients/Git/source transcripts. Both targets completed their initial calls; 44 tests passed inside the harness and 44 passed standalone. Original retained and generated source inventories remained unchanged. |
| Archive verification 20261101T133939774122Z | Source byte/inventory comparison, bundle restoration at c138989, and git fsck passed. Final evidence is committed and packaging rerun afterward; consult each archive manifest for its exact revision. |
| Demo/human CLI smoke check | The launcher printed a working URL/full client command; entering alice and queueing a message through the human CLI succeeded. This is agent evidence only. |
| Agent browser preview | Actual browser displayed incoming and queued messages; screenshot at artifacts/preview/browser.png. This is agent evidence, not user sign-off. |

The regression additions and protocol clarification occurred between generation runs. No frozen assertions were weakened or changed inside a repair loop. No generated client was manually patched. The shared protocol also clarifies the browser's indistinguishable redirect/transport errors; unsupported HTTP methods follow the existing 405 contract.

## CHG-001 execution evidence

| Run / check | Actual result |
|---|---|
| 20261101T142656748004Z | Nine harness guards pass. |
| Generation 20261101T142801177696Z | Python desktop generated on its initial call; 55/55 cases pass before publication; browser source preserved. |
| Agent desktop preview | Actual controls show accepted/queued rows, incoming reply, and exact multiline details; artifacts/changes/CHG-001/desktop.png. |
| Failed proof 20261101T143710332729Z | Preserved FAIL, with 55 harness passes and 54/55 standalone passes; original published clients unaffected. |
| Corrected-fixture acceptance | 55/55 published-client cases pass; exact report at artifacts/changes/CHG-001/corrected-fixture-acceptance.json. |
| Clean proof 20261101T151017779910Z | PASS; fresh clients, frozen assertions, 55/55 inside harness and 55/55 standalone; original tree preserved. Attempts: {"python": 2, "typescript": 2}. |

## Dependencies and environment limits

TypeScript 5.9.3 and @playwright/test 1.56.1 are installed from real npm locks. Chromium 141.0.7390.37 launches and executes the browser suite. Setup locally extracts the missing Ubuntu NSS/NSPR packages into /tmp/reusable-spec-native; browser commands add that directory to their library path. Browser binaries are cached at /tmp/reusable-spec-playwright unless PLAYWRIGHT_BROWSERS_PATH overrides it. For CHG-001 the user installed native python3-tk/xvfb/x11-xkb-utils; x11-utils is also present. Tk 8.6.12 and isolated display creation were verified. No account switch was needed. README and TESTING list package prerequisites and the interactive-display requirement.

Generation is a development-time service dependency. Running committed clients/server requires no model login. Native Windows/macOS and other browser engines remain unverified. The memory-only server requires fresh/reset client stores after each new session, including GUI Stop/Start. One active client per identity is supported. Offline browser asset loading and closed-app delivery remain excluded.

## Source preservation and review

The external original remains AVAILABLE, COMPARED and NOT_INCLUDED, with historical source/guide provenance in [ASSIGNMENT](ASSIGNMENT.md). Current guide revisions do not rewrite those comparison hashes. User-authored input values and manual observations remain preserved; adjacent defaults now reflect completed requests, with previous wording in DECISIONS. CHG-001–004 entries and their actual evidence remain archived in [CHANGES](CHANGES.md). [DESIGN](../DESIGN.md) distinguishes authorship and regeneration ownership.

The user can follow [the two-terminal walkthrough](../TESTING.md#manual-launch-two-terminals-and-one-browser), then record actual M01–M06 observations. Source preference edits should be reconciled before another generation run. The source archive may be prepared for review while those observations remain pending; final sign-off must disclose that state.

## CHG-001 history consolidation

At the user’s request, the five CHG-001 commits after baseline `2b2d205` were consolidated with the README summary and general user confirmation into one commit. Historical revision IDs in test evidence identify the actual pre-squash execution snapshots; their reports are unchanged. The original history is preserved in the verified local bundle `artifacts/history/CHG-001-before-squash.bundle`. See [CHANGES](CHANGES.md) for the consolidation record. No application code or test assertions changed during consolidation.

## CHG-002 execution references

Published-client acceptance: artifacts/changes/CHG-002/acceptance.json (65/65). Guards: artifacts/changes/CHG-002/harness.json (9/9). Clean proof: artifacts/regeneration/20261101T204250502871Z/report.json, inner generation 20261101T204302588941Z, calls per target {"python": 3, "typescript": 3}. See CHANGES and EVIDENCE.json for frozen input/output hashes and failed-run history. The actual server screenshot is artifacts/changes/CHG-002/server-desktop.png; this is agent evidence only.
