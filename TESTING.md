# Setup, verification, and manual walkthrough

Status: Stage 2 implementation and verification. Both clients, server, harness, and retained tests exist. The expanded baseline has 44 passing tests; nine harness guards pass. Clean regeneration passed with all 44 tests in both harness and standalone verification. Current run evidence is in [docs/STATUS.md](docs/STATUS.md).

## What the user should do now

Read [README.md](README.md#what-you-can-edit) and [docs/DECISIONS.md](docs/DECISIONS.md). Leave the 26 preference inputs blank if the defaults fit. Edit a relevant preference cell only if you want different behavior, then ask for Stage 1 reconciliation. You do not need to write protocols, database schemas, or acceptance tests yourself.

Run the manual launch and walkthrough below, then fill M01–M06 with your actual observations. Automated reports and agent previews do not fill those fields. If you change preferences, request reconciliation before regenerating clients.

## Your manual observations

These are facts from your execution, not preferences. Blank observations never select an example as a result. After testing, record actual environment/time/revision, PASS/FAIL with what happened, usability, and evidence. For final user sign-off, the fixed scenario, queued restart, and usability inspection are required; optional fault-injection cases are separate. Agent/automated evidence belongs in STATUS and reports, not these cells.

<!-- USER:BEGIN MANUAL_OBSERVATIONS -->
| ID | Observation | Your observation | Example / behavior if blank |
|---|---|---|---|
| M01 | Actual test environment | | Example: Windows 11, browser and version copied from its About page. Blank: `NOT_RECORDED`. |
| M02 | Actual test time and implementation revision | | Example: local date/time and Git commit hash from this run. Blank: `NOT_RECORDED`. |
| M03 | Required offline scenario result | | Example after verification: PASS; both queued texts appeared once after the specified reconnections. Blank: `NOT_RUN`. |
| M04 | Restart-persistence result | | Example after verification: FAIL; queued text disappeared after the browser reloaded. Blank: `NOT_RUN`. |
| M05 | Usability observations | | Example after verification: I could not distinguish queued from accepted because the labels looked identical. Blank: `NOT_RECORDED`. |
| M06 | Evidence location or reproducible steps | | Example: a test report path plus the exact action sequence that reproduced the failure. Blank: `NOT_RECORDED`. |
<!-- USER:END MANUAL_OBSERVATIONS -->

## Environment and prerequisites

Read-only observations on 2026-11-01 (America/Los_Angeles): Ubuntu 22.04.5 LTS on WSL2 x86_64, Python 3.10.12, Python SQLite 3.37.2, Node.js 22.17.0, npm 10.9.2, Git 2.34.1, global Codex CLI 0.142.5. Version commands exited 0. `codex exec --help` listed the planned adapter flags but emitted a read-only PATH-alias warning. Those Stage 1 checks did not establish model access. Stage 2 subsequently verified local Codex 0.166.0 with requested gpt-6-astra, completed actual client generation, and recorded effective model as UNREPORTED. Prior projects' results are not evidence for this repository.

Baseline requirements: Python >=3.10 with sqlite3/unittest, Node >=22 with npm, Git, and a compatible authenticated coding tool only for generation. No pip package or Python virtual environment is required. Select TypeScript 5.9.3 and retained @playwright/test 1.56.1 with its bundled Chromium; real package-manager locks are committed, and Chromium 141.0.7390.37 launches successfully. On Ubuntu/WSL x86_64, setup extracts missing NSS/NSPR distribution packages into /tmp/reusable-spec-native and browser runs add that directory to their library path. Browser binaries use /tmp/reusable-spec-playwright; set PLAYWRIGHT_BROWSERS_PATH to override the browser location. [TypeScript's release](https://github.com/microsoft/TypeScript/releases/tag/v5.9.3) and [Playwright's release](https://github.com/microsoft/playwright/releases/tag/v1.56.1) identify the pinned upstream versions; the actual application checks are separate local evidence.

Run commands in the project's root using a Linux/WSL terminal. `python3` is used consistently; another platform's equivalent launcher must be verified and documented before claiming support. Windows/native macOS environments are not yet tested. Running already-generated clients does not require model access.

## Commands and results

These entry points are implemented. Command reports distinguish PASS, FAIL, and missing-prerequisite BLOCKED outcomes; the latest actual evidence is recorded in STATUS.

| Entry point | Contract |
|---|---|
| `python3 scripts/check_environment.py` | Read-only versions, missing interpreter/build/browser prerequisites; no implicit install or model request. |
| `python3 scripts/check_environment.py --generation` | Also inspect selected coding-tool executable/help/login readiness; distinguish that from actual preflight model access. |
| `python3 scripts/setup.py` | Install retained test/tool dependencies even with clients absent, and present-target build dependencies; install matching Chromium. Initial npm install creates real locks; later npm ci uses them. |
| `python3 scripts/setup.py --skip-browser-install` | Reuse an already installed matching browser; missing native/browser prerequisites still fail when exercised. |
| `python3 generator/run.py --target all` | Actual isolated generation and validation/publication from current specs. |
| `python3 scripts/build.py --target all` | Python compile/help validation and TypeScript typecheck/build; python/typescript target selection also supported. |
| `python3 scripts/verify.py --suite all` | Build and baseline actual protocol/client/browser checks; excludes harness simulation, clean regeneration, and evolution. |
| `python3 scripts/verify.py --suite protocol` | Retained black-box server cases without generated-client prerequisite. |
| `python3 scripts/verify.py --suite python-interface` | Real CLI startup, validation, durable offline enqueue, snapshots, and bounded shutdown. |
| `python3 scripts/verify.py --suite harness` | AT-18 guardrail tests using controlled runner fixtures, no live agent calls. |
| `python3 scripts/verify.py --suite all --report artifacts/manual-verification.json` | Same baseline checks with a requested machine-readable report location. Other suites accept --report too. |
| `python3 scripts/demo.py --port 8765` | Start server, print browser URL and a copy-ready CLI command with a fresh state directory; bind failure does not kill another process. |
| `python3 scripts/regenerate_check.py` | AT-15 proof in a fresh retained-input workspace; leave original source/stores unchanged. |
| `python3 scripts/package.py` | Require committed intended source/clean tree; create source archive and real Git history, excluding runtime/cache/credential data; document exact restoration. |

Server entry: `python3 server/main.py --host 127.0.0.1 --port 8765 --static-dir generated/typescript-web/dist`. Tests use --port 0. On readiness emit one JSON stdout line with `event:"ready"` and actual `origin`; diagnostics go to stderr. Bind failure exits nonzero. Ctrl-C terminates the owned server cleanly. No client/network outage test kills the server to simulate a client disconnect.

Setup/build/test scripts record sanitized commands, return codes, times, counts, and prerequisites. Missing prerequisites return a nonzero BLOCKED result; collected assertion failures return FAIL. Zero tests or skipped required cases fail. Do not bypass a browser-library or sandbox restriction; record the real failure and use an authorized compatible setup. A version/help check is not an authenticated model preflight.

## Automated verification

To run the retained checks:

```sh
python3 scripts/setup.py
python3 scripts/check_environment.py
python3 scripts/verify.py --suite all
python3 scripts/verify.py --suite harness
python3 scripts/regenerate_check.py
```

The baseline runner uses Python unittest under tests/protocol and Playwright under tests/browser. Required case mapping is in [ACCEPTANCE.md](specs/ACCEPTANCE.md#required-automated-cases); no hard-coded final executable test count is claimed before collection. Tests allocate their own ports, external per-client proxies, CLI stores, and browser contexts. Reports include spec/test fingerprints and failures; Playwright traces/screenshots are retained for failures. Do not edit tests in a generator repair. Whole-test retries do not turn a flaky result into a clean pass.

Model tool installation/preflight is needed for generation/proof, not for replaying ordinary acceptance against committed clients. The outer proof excludes old generated source, Git objects, old sessions, stores, and source-bearing transcripts. Baseline verification never invokes regeneration recursively. No evolution feature is active; its execution is deferred until separately authorized.

## Manual launch: two terminals and one browser

Open a terminal in this project's directory (the folder containing README.md) and run:

```sh
python3 scripts/setup.py
python3 scripts/build.py --target all
python3 scripts/demo.py --port 8765
```

Keep this first terminal running. The helper must print `In another terminal:` followed by a complete command beginning with `python3 generated/python-client/main.py`, including --server and a fresh --state-dir under var/demo/<run-id>/alice. In VS Code, open a second terminal with the + button; change to this same project directory. Copy only the command after the prefix from the first terminal, paste it in the second, and press Enter. Do not paste a placeholder run-id or the words “In another terminal.”

At the client's `Username:` prompt, type `alice` and press Enter. Commands below are typed at the running client's prompt, not the shell. Open the printed origin, normally http://127.0.0.1:8765, in a fresh private browser window and log in as `bob`. For a previously used browser store, use its Reset local store then Confirm reset controls before the new session. The server is memory-only; a restarted server requires fresh/reset client stores even when an old cursor appears valid.

## Manual interoperability walkthrough

Keep the same server alive throughout. Record your actual observations in M03/M05/M06, with environment and date/time/commit in M01/M02.

| Step | What to do | What to verify |
|---|---|---|
| 1 | Alice terminal: `send bob Hi Bob, I have something important to tell you` | Alice's row becomes accepted by server; Bob's inbox shows the exact greeting from alice once. |
| 2 | Browser recipient alice, text `What is it?`, click Send | Bob's outgoing row becomes accepted by server; Alice displays the reply from bob once. |
| 3 | Alice: `transport offline`, then `send bob Alice queued while offline`, then `outbox` | New row is queued with exact text and an ID. Earlier accepted row remains. |
| 4 | Browser Development transport offline; send alice `Bob queued while offline` | Bob's new outgoing row stays queued; neither queued message is newly accepted yet. |
| 5 | Alice: `transport online`, inspect `outbox` | Her queued row becomes accepted while Bob remains offline. |
| 6 | Alice: `transport offline` after that acceptance | Server remains running; Alice stops new network requests. |
| 7 | Browser Development transport online | Bob receives Alice's queued text once and his own queued row becomes accepted. Either observation may happen first. |
| 8 | Alice: `transport online`, then `inbox` | Alice receives Bob's queued text once. Each inbox has the two expected texts in order. |

Use `status`, `outbox`, and `inbox` to inspect the real CLI state. Allow at most 30 seconds per transition while the clients are active; record a failure with the action and observed state if the condition does not arrive. A healthy server or a send acknowledgment alone does not prove the recipient displayed a message.

For M04, keep the server alive, put Alice offline, send bob `Restart persistence check`, record its queued ID/text, then `quit`. Rerun the same printed CLI command with the same --state-dir and add `--transport offline`. Identity restores without a new prompt; outbox must retain the original queued ID/text. Reconnect and verify Bob sees it once. Test browser reload persistence through the retained API-only fault fixture, or record that separate browser manual check as NOT_RUN; normal offline-first asset reload is excluded. Automated AT-09 is required for both clients.

For M05, inspect queued versus accepted versus failed labels and visible incoming sender/text without consulting transport logs. Record real usability problems, including whether whitespace/newlines are readable. Agent-scripted walkthroughs are separate evidence and never fill your table.

Quit CLI with `quit`; stop server with Ctrl-C after testing. For a new server session, use a new demo state directory or explicitly reset a stopped CLI with its own --state-dir and --reset-state --yes. Keep the exact state directory for normal persistence tests; do not delete a broad directory or unrelated browser storage.

## Reports, archive, and readiness

Write run evidence under ignored artifacts/<category>/<run-id>/ and concise committed summaries in docs/STATUS.md / docs/ASSIGNMENT_REVIEW.md. Reports identify actual revision/input/test hashes, versions, selected model versus reported effective model, scope, attempts, exit codes, counts, and unverified behavior. Never include credentials, raw environment dumps, or personal stores.

Packaging includes committed clients, retained inputs/scripts/tests/manifests/locks, and real Git history. A source snapshot plus Git bundle is acceptable if the archive includes exact clone/checkout instructions. Verify unpacked source byte-for-byte against the recorded revision and test bundle restoration/Git integrity. Exclude caches, node_modules, dist, stores, auth files, old source-bearing transcripts, and recursively included archives. A review archive can exist while human checks remain pending; final release readiness requires declared manual sign-off and archive verification.

Optional OF-01/OF-02 forced crash/write-failure tests and any evolution run remain explicitly NOT_RUN until performed. Do not silently turn them into baseline requirements or report them as covered by an ordinary successful run.
