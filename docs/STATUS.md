# Project status and evidence

Updated 2026-11-01 (America/Los_Angeles). The agent authored specifications and retained infrastructure/tests; actual isolated Codex harness calls authored both clients. Blank USER preferences are not user-authored answers, and automated/agent checks do not fill manual observations.

## Completion states

| Area | State | Evidence / remaining work |
|---|---|---|
| Stage 1 documentation | COMPLETE | All 16 required documents, source comparison, catalog forms, and contracts completed; current docs reconciled with implementation |
| Preferences | COMPLETE | All 26 optional cells unchanged/blank; effective defaults in DECISIONS; no unresolved user-choice conflict |
| Environment | VERIFIED for this environment | Ubuntu 22.04.5/WSL2 x86_64; Python 3.10.12, SQLite 3.37.2, Node 22.17.0, npm 10.9.2, Git 2.34.1 |
| Coding-tool access | PASS | Project-local Codex 0.166.0, requested gpt-6-astra, effective UNREPORTED; authenticated writable preflight and real generation calls |
| Implementation | COMPLETE | Retained components and generated clients build; actual generation, required checks, clean proof, and operating documentation complete |
| Automated baseline | PASS | 44 tests: nine protocol, four CLI interface, 31 actual-client/browser cases; zero failures/skips/flaky results |
| Harness guards | PASS | Nine AT-18 tests, including inventory/path violations, incomplete events, invalid reports, timeout, input allowlisting, and publication rollback |
| Clean regeneration | PASS | Run 20261101T133420994052Z recreated both clients, passed 44 tests in the harness and again standalone, and preserved the original tree |
| Evolution | NOT_RUN — deferred | No selected request or isolated experiment; active extensions and FUTURE queue empty |
| Optional storage/crash injections | NOT_RUN — deferred | OF-01/OF-02 remain disclosed optional executions; normal restart, malformed-page rollback, and unsupported-store checks pass |
| User manual review | PENDING | M01/M02/M05/M06 NOT_RECORDED; M03/M04 NOT_RUN; every source observation cell remains blank |
| Review archive | VERIFIED | Source inventory, byte equality, Git bundle clone/checkout, and git fsck passed; each archive manifest records its exact committed revision |
| Final release readiness | NOT_READY — manual review pending | Automated implementation gates and archive verification pass; the required user observations remain blank |

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

## Dependencies and environment limits

TypeScript 5.9.3 and @playwright/test 1.56.1 are installed from real npm locks. Chromium 141.0.7390.37 launches and executes the browser suite. Setup locally extracts the missing Ubuntu NSS/NSPR packages into /tmp/reusable-spec-native; browser commands add that directory to their library path. Browser binaries are cached at /tmp/reusable-spec-playwright unless PLAYWRIGHT_BROWSERS_PATH overrides it. No system-wide installation or account switch was performed.

Generation is a development-time service dependency. Running the committed clients/server requires no model login. Native Windows/macOS and other browser engines are unverified. The server remains memory-only; each new server process requires fresh/reset client stores. One active client instance per identity is supported. Offline browser asset loading and closed-app delivery remain excluded.

## Source preservation and review

The external original remains AVAILABLE, COMPARED, and NOT_INCLUDED, with provenance in [ASSIGNMENT](ASSIGNMENT.md). The construction guide and external-source hashes are unchanged. Source forms and the empty request/completion histories are preserved. Retained source and generated ownership are distinguished in [DESIGN](../DESIGN.md).

The user can follow [the two-terminal walkthrough](../TESTING.md#manual-launch-two-terminals-and-one-browser), then record actual M01–M06 observations. Source preference edits should be reconciled before another generation run. The source archive may be prepared for review while those observations remain pending; final sign-off must disclose that state.
