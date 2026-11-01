# Setup, verification, and manual walkthrough

Status: CHG-002 complete. All 65 acceptance cases (55 existing plus ten server GUI cases) and nine harness guards pass. Clean regeneration passes all 65 tests inside the harness and again standalone. Current run evidence is in [docs/STATUS.md](docs/STATUS.md).

## What the user should do now

Read [README.md](README.md#what-you-can-edit) and [docs/DECISIONS.md](docs/DECISIONS.md). Leave the 26 preference inputs blank if the resolved choices fit; CHG-001 explicitly supersedes the original Python CLI default. Edit a relevant preference cell only if you want different behavior, then ask for Stage 1 reconciliation. You do not need to write protocols, database schemas, or acceptance tests yourself.

Run the manual launch and walkthrough below, then fill M01–M06 with your actual observations. Automated reports and agent previews do not fill those fields. If you change preferences, request reconciliation before regenerating clients.

## Your manual observations

On 2026-11-01 (America/Los_Angeles), the user confirmed: “I confirmed that it works well.” This records general user confirmation; no individual scenario results or environment details were supplied, so M01–M06 remain unchanged.

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

Baseline requirements: Python >=3.10 with sqlite3/unittest/tkinter and native Tcl/Tk 8.6, Node >=22 with npm, Git, and a compatible authenticated coding tool only for generation. No pip package or Python virtual environment is required. Select TypeScript 5.9.3 and retained @playwright/test 1.56.1 with its bundled Chromium; real package-manager locks are committed, and Chromium 141.0.7390.37 launches successfully. On Ubuntu/WSL x86_64, setup extracts missing NSS/NSPR distribution packages into /tmp/reusable-spec-native and browser runs add that directory to their library path. Browser binaries use /tmp/reusable-spec-playwright; set PLAYWRIGHT_BROWSERS_PATH to override the browser location. [TypeScript's release](https://github.com/microsoft/TypeScript/releases/tag/v5.9.3) and [Playwright's release](https://github.com/microsoft/playwright/releases/tag/v1.56.1) identify the pinned upstream versions; the actual application checks are separate local evidence.

Desktop prerequisites on Ubuntu/WSL:

```sh
sudo apt-get update
sudo apt-get install -y python3-tk xvfb x11-xkb-utils x11-utils
python3 -m tkinter
```

The last command should open a Tk test window; close it after checking. Tkinter/Tcl/Tk are runtime requirements for the GUI. Xvfb, xkbcomp (x11-xkb-utils), and xwininfo (x11-utils) are required by automated desktop verification. A visible desktop display such as working WSLg is required for manual use. Automated checks start an isolated Xvfb display. Setup verifies the prerequisites and reports missing packages as BLOCKED; it does not run privileged package installation. The user enters any sudo password in their own terminal. Python --machine, --help and stopped-store reset do not require a display.

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
| `python3 scripts/verify.py --suite server-gui` | Retained server window lifecycle and HTTP monitoring checks on an isolated display. |
| `python3 scripts/verify.py --suite harness` | AT-18 guardrail tests using controlled runner fixtures, no live agent calls. |
| `python3 scripts/verify.py --suite all --report artifacts/manual-verification.json` | Same baseline checks with a requested machine-readable report location. Other suites accept --report too. |
| `python3 server/gui.py` | Open the optional server control window, initially stopped; Start/Stop and monitoring use the same retained HTTP server. |
| `python3 scripts/demo.py --port 8765` | Start server, print browser URL and a copy-ready desktop launch command with a fresh state directory; bind failure does not kill another process. |
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

The baseline runner uses Python unittest under tests/protocol and Playwright under tests/browser. Required case mapping is in [ACCEPTANCE.md](specs/ACCEPTANCE.md#required-automated-cases); no hard-coded final executable test count is claimed before collection. Tests allocate their own ports, external per-client proxies, Python stores, and browser contexts. Reports include spec/test fingerprints and failures; Playwright traces/screenshots are retained for failures. Do not edit tests in a generator repair. Whole-test retries do not turn a flaky result into a clean pass.

Model tool installation/preflight is needed for generation/proof, not for replaying ordinary acceptance against committed clients. The outer proof excludes old generated source, Git objects, old sessions, stores, and source-bearing transcripts. Baseline verification never invokes regeneration recursively. CHG-001 adds GUI-01–06 and is verified through the ordinary harness; generic orchestration and prompt fingerprints are compared before/after.

## Manual launch: two terminals and one browser

Open a terminal in this project's directory (the folder containing README.md) and run:

```sh
python3 scripts/setup.py
python3 scripts/build.py --target all
python3 scripts/demo.py --port 8765
```

Keep this first terminal running. The helper must print `In another terminal:` followed by a complete command beginning with `python3 generated/python-client/main.py`, including --server and a fresh --state-dir under var/demo/<run-id>/alice. In VS Code, open a second terminal with the + button; change to this same project directory. Copy only the command after the prefix from the first terminal, paste it in the second, and press Enter. Do not paste a placeholder run-id or the words “In another terminal.”

A desktop window titled **Local Messenger - Python** opens. Enter `alice` in Username and click **Log in**. Enter the remaining actions in the graphical controls. Open the printed origin, normally http://127.0.0.1:8765, in a fresh private browser window and log in as `bob`. For an existing browser store, use Reset local store then Confirm reset. The server is memory-only; a restarted server requires fresh/reset client stores even when an old cursor appears valid.

## Manual interoperability walkthrough

Keep the same server alive throughout. Record actual observations in M03/M05/M06, with environment/date/time/commit in M01/M02. Both clients expose Development transport with online/offline values.

| Step | What to do | What to verify |
|---|---|---|
| 1 | Desktop recipient `bob`, text `Hi Bob, I have something important to tell you`; click Send | Alice's outgoing row becomes accepted by server; Bob's inbox shows the exact greeting from alice once. |
| 2 | Browser recipient `alice`, text `What is it?`; click Send | Bob's outgoing row becomes accepted by server; Alice's inbox shows the reply from bob once. |
| 3 | Desktop Development transport offline; send bob `Alice queued while offline` | The new row stays queued with its original text/ID; the earlier accepted row remains. |
| 4 | Browser Development transport offline; send alice `Bob queued while offline` | Bob's new row stays queued; neither queued message is newly accepted. |
| 5 | Desktop Development transport online | Alice's queued row becomes accepted while Bob remains offline. |
| 6 | Desktop Development transport offline after that acceptance | Server remains running; Alice stops new network requests. |
| 7 | Browser Development transport online | Bob receives Alice's queued text once and his own queued row becomes accepted. Either observation may happen first. |
| 8 | Desktop Development transport online | Alice receives Bob's queued text once. Each inbox contains the two expected texts in order. |

Inspect inbox/outgoing rows and connection/error labels. Widen the desktop Message ID column by dragging its heading border when recording the full identifier; use the horizontal scrollbar for additional columns. Select a desktop row to read its exact full text in the detail pane, including spaces/newlines. Allow at most 30 seconds per transition while clients are active. Record failures with actions and observed states; a server health response alone is not proof of display.

For M04, keep the server alive, put Alice offline, send bob `Restart persistence check`, and record the queued ID/text. Close the desktop window. Rerun the same printed command with the same --state-dir and append `--transport offline`. Identity and original queued ID/text must restore. Select online and verify Bob receives it once. Browser reload persistence uses API-only outages with static assets reachable; record a separate unperformed manual browser check as NOT_RUN. Automated AT-09 remains required for both clients.

For M05, compare both graphical workflows. Verify invalid recipients/empty messages show errors and preserve drafts; valid Unicode/spaces/newlines display exactly. In a separate fresh store if needed, verify Reset local store followed by Cancel preserves identity/messages, and Confirm reset returns to login and clears only the selected application's data. Inspect queued versus accepted labels and incoming sender/text without logs. Permanent failure and in-flight shutdown are also covered by retained GUI tests; do not invent a manual observation for an unperformed fault injection.

Close the desktop window to quit; stop the server with Ctrl-C afterward. For a new server session use a fresh demo directory or explicitly reset the stopped Python client with its exact --state-dir and --reset-state --yes. Keep the same state directory during normal persistence testing. Do not delete unrelated files or browser storage.

## Desktop automated coverage

The retained `tests/gui_driver.py` constructs the same generated DesktopApp as main.py and operates real Tk Entries, Text widgets, Buttons, Comboboxes, and Treeviews. It reads visible controls and may inspect SQLite read-only for cursor assertions; it never invokes backend messaging operations. GUI-01–06 cover invalid input, exact details, both-role offline interoperability, legacy version-1 stores, reopen persistence, canceled/confirmed reset, actually held old-identity GET responses during reset, responsive editing, default GUI launch with closed stdin, shutdown, and visible failures. Existing machine tests remain the protocol oracle for nonprinting scalar and wire boundaries. All GUI tests run in `--suite all` and in clean regeneration; no graphical failure may be hidden by substituting machine-only results.

## Reports, archive, and readiness

Write run evidence under ignored artifacts/<category>/<run-id>/ and concise committed summaries in docs/STATUS.md / docs/ASSIGNMENT_REVIEW.md. Reports identify actual revision/input/test hashes, versions, selected model versus reported effective model, scope, attempts, exit codes, counts, and unverified behavior. Never include credentials, raw environment dumps, or personal stores.

Packaging includes committed clients, retained inputs/scripts/tests/manifests/locks, and real Git history. A source snapshot plus Git bundle is acceptable if the archive includes exact clone/checkout instructions. Verify unpacked source byte-for-byte against the recorded revision and test bundle restoration/Git integrity. Exclude caches, node_modules, dist, stores, auth files, old source-bearing transcripts, and recursively included archives. A review archive can exist while human checks remain pending; final release readiness requires declared manual sign-off and archive verification.

Optional OF-01/OF-02 forced crash/write-failure tests remain explicitly NOT_RUN until performed. Do not silently turn them into baseline requirements or report them as covered by an ordinary successful run.

The retained fault proxy uses a fresh upstream connection for each request to the closing local server, records asset failures in startup diagnostics, and never retries a failed static asset to conceal a failure. Delayed-receive assertions first observe a real held GET response. Failed clean proofs remain in execution history even after a later corrected run passes.

## Server GUI manual verification (CHG-002)

Use the same native Tk/Xvfb/X11 packages listed above; no new Python or npm dependency is required. From the project root run `python3 scripts/build.py --target all`, then `python3 server/gui.py`. The latter opens **Local Messenger - Server**; subsequent server operation uses the window. Close any old demo server before using its port, or choose another free port. Port `0` allocates one and the window displays the actual URL.

1. Verify the initial **Stopped** state. Keep port `8765` and the default browser assets directory, then click **Start**. Expect **Running**, a loopback URL and a new session ID. Start/configuration are disabled while running; Stop and Open browser are enabled.
2. Click **Open browser**, use a fresh private browser context, and log in as `bob`. Launch the Python GUI with the displayed URL and a fresh state directory, for example `python3 generated/python-client/main.py --server http://127.0.0.1:8765 --state-dir "$(mktemp -d)"`, then log in as `alice`. Replace the port when necessary.
3. Run the eight-step interoperability walkthrough above, keeping this server window running. Both clients should receive each message once. The unique accepted-message count should be four; requests can be larger because clients poll. Select a monitor row to inspect exact text, sender, recipient, message ID and recipient sequence. Test multiline/Unicode text as well. The monitor displays the latest 200 messages/responses; total counts cover the whole session.
4. Click **Stop**. Expect **Stopped**, a cleared listening URL and monitoring lists, and disabled Open browser. A new client send should remain queued because this endpoint is unavailable. Stopping the server is a separate lifecycle check, not the way to simulate a single client's outage.
5. Close both old clients. Click **Start** again; expect a different session ID and empty counters/messages. Launch Python with a new state directory and use a fresh private browser context (close all prior private windows), or explicitly reset the old client stores. Exchange new messages. Cross-session automatic client recovery is not supported.
6. Close the server window while running; it should close and release its port within six seconds. Reopening the GUI starts in **Stopped** state. Invalid ports/missing browser assets must produce visible guidance. If a different process already owns the chosen port, Start should fail visibly while leaving that process alone; choose a free port and retry.

Record actual observations separately from automated evidence. On 2026-11-01 (America/Los_Angeles), the user confirmed CHG-002: “I found it works well.” This records general confirmation; individual scenario results were not supplied, so M01–M06 remain unchanged. Required automated SG-01–SG-06 include eight server-widget/HTTP tests and two client integration cases, and run in the full acceptance suite and clean regeneration. Focused command: `python3 scripts/verify.py --suite server-gui`.


## Shared directory and user activity (CHG-003)

Use the server GUI launch above and fresh client stores for Alice (Python) and Bob (browser). The existing native packages suffice; no additional dependencies are required. These instructions describe the new contract; current execution status is in [STATUS](docs/STATUS.md).

1. Keep both clients online. Each recipient list should show the other username, excluding itself. Filter the list, select a recipient, and verify the Recipient field changes while the message draft remains intact. Selection alone must not send. Manual valid usernames remain usable even when absent from the list.
2. In the server window select **Users**, filter/select Alice or Bob, and inspect **Sent**, **Received**, and **Queued**. Select a message row to read its exact full text. Operator selection and Refresh never acknowledge messages.
3. Put Bob offline, then send Bob a message from Alice. After server acceptance, Alice's Sent list and Bob's Queued list show it. Bob's Received list must not include it yet. Reconnect Bob: after durable local receipt and acknowledgment, the message moves from Bob's Queued to Received; Alice's Sent status becomes received. This means durable client receipt, not that a person read the message.
4. Put Alice offline and compose another message. It stays in her local outbox and is absent from server activity until accepted after reconnection. The server notice says **Offline client queues: unknown**. Cached client directory information is stale while offline. After at least 15 seconds without an announcement, the server Users tab **Status** becomes **Offline** (clients still say **not recently seen**); presence is advisory and must not prevent selection or sending.
5. Reopen a client with the same store while this server remains alive. Persisted inbox messages remain and receipt reporting resumes without duplicates. Resetting a client clears its transient directory and local messages; a delayed old response must not restore them. Reset does not revoke historical server acknowledgments. Stop/Start the server clears directory and receipt state; use fresh/reset client stores for the new session.

Automated DIR-01–08 cover directory validation, presence expiry, monotonic receipts, operator read-only activity, both client interfaces, auxiliary-route failures, malformed-page rollback, and delayed-response reset guards. Run `python3 scripts/verify.py --suite all`; `--suite protocol` and `--suite server-gui` provide focused retained-server checks. Full clean proof remains `python3 scripts/regenerate_check.py`. New route faults are recorded separately from legacy message-route history so original messaging assertions retain their meaning.


### Server Online/Offline status

Open the server **Users** tab after Alice and Bob log in. Their **Status** should become **Online** after their next successful heartbeat. Close one client or set its Development transport to offline while leaving the server running. Within 15 seconds of its last heartbeat, plus the GUI refresh interval (at most one second), its status becomes **Offline** automatically. Reopen/reconnect the same client; after its next heartbeat, status returns to **Online**. A known recipient who has never connected is Offline. Status reflects recent heartbeats, not guaranteed reachability or message acknowledgment. The focused command `python3 scripts/verify.py --suite server-gui` tests this display and the existing server controls.
