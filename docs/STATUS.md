# Project status and evidence

Updated 2026-11-01 (America/Los_Angeles). The agent authored specifications and retained infrastructure/tests; actual isolated Codex harness calls authored both clients. Blank USER preferences are not user-authored answers, and automated/agent checks do not fill manual observations.

## CHG-001 complete

The Python desktop client was generated through the actual harness and passed 55 acceptance tests; nine harness guards also pass. Independent GUI checks cover both-role messaging, exact text, legacy stores, restart, actual held-response reset, validation, responsiveness and shutdown. Agent visual inspection passed; user observations remain separate. Clean proof 20261101T151017779910Z recreated both clients and passed 55 tests inside the harness and again standalone while preserving the original tree. The original request and actual evidence were archived in [CHANGES](CHANGES.md) before removing its completed active entry.

Earlier clean proof 20261101T143710332729Z remains FAIL: TypeScript's initial compilation conflict was repaired, but standalone browser startup lost main.js with ERR_EMPTY_RESPONSE (54/55). Twelve focused diagnostic repetitions and 500 HTTP probes did not reproduce the transport failure. Retained correction aeb2441 disables upstream pooling for the closing server, adds body-free asset diagnostics, and makes GUI-04 assert an actual held GET response. No retry, skip, relaxed assertion, or increased deadline was used to turn the failure into success. Revised published-client acceptance and the new clean proof pass.

## Completion states

| Area | State | Evidence / remaining work |
|---|---|---|
| Stage 1 documentation | COMPLETE | All 16 required documents, source comparison, catalog forms, and contracts completed; current docs reconciled with implementation |
| Preferences | COMPLETE | All 26 optional cells unchanged/blank; effective defaults and explicit CHG-001 override in DECISIONS; no unresolved user-choice conflict |
| Environment | VERIFIED for this environment | Ubuntu 22.04.5/WSL2 x86_64; Python 3.10.12, SQLite 3.37.2, Node 22.17.0, npm 10.9.2, Git 2.34.1; Tk 8.6.12; native GUI prerequisites installed by the user |
| Coding-tool access | PASS | Project-local Codex 0.166.0, requested gpt-6-astra, effective UNREPORTED; authenticated writable preflight and real generation calls |
| Implementation | COMPLETE | Retained components and generated clients build; actual generation, required checks, clean proof, and operating documentation complete |
| Automated baseline | PASS | 55 tests: nine protocol, four machine interface, 31 existing client/browser cases, 11 desktop cases; zero failures/skips/flaky results |
| Harness guards | PASS | Nine AT-18 tests, including inventory/path violations, incomplete events, invalid reports, timeout, input allowlisting, and publication rollback |
| Clean regeneration | PASS | Run 20261101T151017779910Z recreated both clients, passed 55 tests in the harness and again standalone, and preserved the original tree |
| Evolution | PASS — CHG-001 | Revised desktop contracts/tests/configuration pass through the unchanged generic runner/prompt; no protocol extension or SQLite migration |
| Optional storage/crash injections | NOT_RUN — deferred | OF-01/OF-02 remain disclosed optional executions; normal restart, malformed-page rollback, and unsupported-store checks pass |
| User manual review | GENERAL CONFIRMATION RECEIVED | On 2026-11-01 the user stated “I confirmed that it works well.” Detailed M01–M06 observations were not supplied; source cells remain blank. |
| Review archive | VERIFIED | CHG-001 source inventory (63 files), byte equality, Git bundle restoration and git fsck pass; run 20261101T153354714666Z. Packaging is rerun after final evidence commits; each manifest identifies its exact revision. |
| Final release readiness | NOT_READY — detailed observations and current archive pending | General user confirmation received; detailed M01–M06 observations remain blank. Existing archive verification applies to the recorded pre-squash revision; the consolidated revision has not been packaged. |

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

Generation is a development-time service dependency. Running the committed clients/server requires no model login. Native Windows/macOS and other browser engines are unverified. The server remains memory-only; each new server process requires fresh/reset client stores. One active client instance per identity is supported. Offline browser asset loading and closed-app delivery remain excluded.

## Source preservation and review

The external original remains AVAILABLE, COMPARED, and NOT_INCLUDED, with provenance in [ASSIGNMENT](ASSIGNMENT.md). The construction guide and external-source hashes are unchanged. All source USER blocks are preserved. CHG-001 is archived with its exact original wording and evidence; its completed active entry was then removed, preserving queue markers and examples. Retained source and generated ownership are distinguished in [DESIGN](../DESIGN.md).

The user can follow [the two-terminal walkthrough](../TESTING.md#manual-launch-two-terminals-and-one-browser), then record actual M01–M06 observations. Source preference edits should be reconciled before another generation run. The source archive may be prepared for review while those observations remain pending; final sign-off must disclose that state.

## CHG-001 history consolidation

At the user’s request, the five CHG-001 commits after baseline `2b2d205` were consolidated with the README summary and general user confirmation into one commit. Historical revision IDs in test evidence identify the actual pre-squash execution snapshots; their reports are unchanged. The original history is preserved in the verified local bundle `artifacts/history/CHG-001-before-squash.bundle`. See [CHANGES](CHANGES.md) for the consolidation record. No application code or test assertions changed during consolidation.
