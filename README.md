# Reusable Spec-Driven Code Generator

A reusable agentic harness that turns written specifications into independent Python and TypeScript clients. A local messaging application provides a concrete example of offline queues, durable client state, and interoperability.

**Status: CHG-001 and CHG-002 complete.** All 65 acceptance tests and nine harness guards pass. Clean regeneration passed the same 65 tests inside the harness and again standalone. The user confirmed that both changes work well; detailed manual observations remain unrecorded. [Status and evidence](docs/STATUS.md) records actual results.

## Change summary

- **CHG-001:** Replaced the Python terminal interface with a desktop GUI, preserved existing stored data and the headless interface, and added GUI tests and setup instructions. Automated verification and clean regeneration passed.
- **CHG-002:** Added a desktop window to start, stop, and monitor the local server, with session status, message activity, and GUI integration tests. Automated verification and clean regeneration passed.

See [docs/CHANGES.md](docs/CHANGES.md) for the full change history and verification evidence.

## Start here

To try the committed application, follow the local demonstration below and [TESTING.md](TESTING.md). Read [the resolved choices](docs/DECISIONS.md) and the edit map if you want to change behavior. Leave preference cells blank when the defaults fit; you do not need to author wire protocols or database schemas.

The selected interfaces are a Python desktop GUI, a plain TypeScript browser client, a small local Python server, and Codex-driven generation. Both clients persist identity and messages. The server retains data only during one running server session; each new server session requires explicit fresh/reset demo client stores. CHG-001 replaces the Python human terminal interface; the headless machine interface remains for protocol tests.

To bootstrap a separate new project, begin with the canonical [Instruction_for_Agent.md](Instruction_for_Agent.md). This README is the resulting operating guide; it is not a second construction template or preference form. Reading Markdown does not execute a workflow.

## What you can edit

Edit the `Your input` or `Your observation` cells inside the paired USER markers. Keep field IDs and examples. Blank, whitespace-only, TBD, and — preferences select adjacent defaults. Explicit false, 0, and none are real choices and may need compatibility reconciliation. Blank observations are missing facts, never successful example results.

| File | Section key / fields | What you write | Adjacent example |
|---|---|---|---|
| [specs/PRODUCT.md](specs/PRODUCT.md#your-product-choices) | PRODUCT_CHOICES / P01–P11 | Desired product, interfaces, scope, and visible behavior | P04: interface preference (CHG-001 selects Python desktop GUI) |
| [specs/ACCEPTANCE.md](specs/ACCEPTANCE.md#your-acceptance-expectations) | ACCEPTANCE_CHOICES / A01–A05 | Expected scenarios and outcomes | A02: lost acknowledgment still produces one inbox entry |
| [DESIGN.md](DESIGN.md#your-design-priorities) | DESIGN_CHOICES / D01–D05 | Priorities and tradeoffs | D01: offline correctness and regeneration before polish |
| [AGENTS.md](AGENTS.md#your-working-preferences) | WORKFLOW_CHOICES / W01–W05 | Tool and working preferences | W01: Codex; another supported choice is Claude Code |
| [TESTING.md](TESTING.md#your-manual-observations) | MANUAL_OBSERVATIONS / M01–M06 | Actual observations after personally testing Stage 2 | M03: the observed offline scenario result; blank means NOT_RUN |

All 26 preference cells and six observation cells are initially blank. Effective defaults and the later CHG-001 interface override are recorded separately in docs/DECISIONS.md; unchanged blank cells do not undo that request. The agent maintains the technical portions of these documents, PROTOCOL/PYTHON/TYPESCRIPT, generation instructions, status, and traceability. Changes to preferences are reconciled across those documents before implementation. The user does not need to edit wire schemas or generated source to request different behavior.

## Stages and copy-ready instructions

Stage 1 authors the complete Markdown contracts and stops. Review is your opportunity to edit preferences. Stage 2 separately implements retained components, generates clients, verifies behavior and clean regeneration, and prepares honest evidence. Manual review follows actual implementation and stays separate from automated results.

For a new project or an explicitly requested Stage 1 rerun:

```text
Read Instruction_for_Agent.md and execute Stage 1 only.
Preserve existing USER inputs, resolve blank preferences from their defaults,
and create or reconcile all required Markdown documents. Check consistency,
show the editable USER sections, and stop before implementation.
```

After changing preference cells:

```text
I updated the USER sections. Reconcile all Stage 1 documents with my changes.
Preserve my wording and unrelated decisions. Update affected specifications,
acceptance cases, and planned procedures. Report actual conflicts and stop before code.
```

When the specifications fit:

```text
Start Stage 2 using Instruction_for_Agent.md, AGENTS.md, and the completed
specifications. Reconcile edited inputs, implement the retained components,
generate both clients through the harness, and verify baseline behavior and
clean regeneration. Record actual results, provenance, and any pending user review.
```

These are messages to the coding agent, not shell commands. Reviewing a document does not start a stage. An empty FUTURE queue does not authorize features or experiments.

## Where everything belongs

The implementation paths below exist. Only the two generated client directories are replacement boundaries.

| Location | Role / regeneration ownership |
|---|---|
| Instruction_for_Agent.md | Retained construction process and field catalog |
| README.md, AGENTS.md, DESIGN.md, GENERATE.md, TESTING.md | Retained navigation, agent rules, rationale, generation and test contracts |
| FUTURE.md / docs/CHANGES.md | User's active requests / completed request evidence; archive completed requests with actual evidence |
| specs/PRODUCT.md, PROTOCOL.md, ACCEPTANCE.md | Shared intent, wire behavior, and independent acceptance contract |
| specs/SERVER.md | Retained server desktop controls, monitoring, and session lifecycle |
| specs/PYTHON.md / TYPESCRIPT.md | Platform-specific interfaces, storage, and lifecycle |
| docs/DECISIONS.md / STATUS.md | Effective choices, provenance, readiness and actual evidence |
| docs/ASSIGNMENT.md / ASSIGNMENT_REVIEW.md | Neutral requirements-source summary and criterion-to-evidence mapping |
| generator/ | Retained generic orchestration, configuration, prompts, and tool adapter |
| server/ | Retained local server and optional desktop controls |
| tests/ | Retained independent tests and fault fixtures |
| scripts/ | Retained environment/setup/build/test/demo/proof/package commands |
| generated/python-client/ | **Generated deletion boundary** for Python source and target declarations |
| generated/typescript-web/ | **Generated deletion boundary** for browser source and target declarations |
| artifacts/ | Disposable generation/build/test reports, candidates, and caches; excluded from source publication |

Do not delete the server, tests, scripts, specs, or harness when checking regeneration. Source must be recreated through the coding tool; restoring previous clients from Git or an archive does not prove generation. The clean proof uses a separate retained-input workspace and preserves your current tree.

## Setup, generation, and verification

Verified environment: Ubuntu 22.04/WSL2, Python 3.10.12, Node 22.17.0, npm 10.9.2, and Chromium 141.0.7390.37. Setup installs exact TypeScript/Playwright and project-local Codex 0.166.0 dependencies from real npm locks. It can extract missing Ubuntu NSS/NSPR browser libraries into /tmp/reusable-spec-native without system installation. Other operating systems are unverified.

Install [desktop prerequisites](#desktop-prerequisites-ubuntu--wsl) before the setup/verification commands below.

Generation uses requested model gpt-6-astra, successfully checked with the current account; the service did not report an effective model identifier. Each harness run repeats a bounded authenticated preflight. On another machine, authenticate the local CLI if needed with `generator/codex/node_modules/.bin/codex login`. Running committed clients requires no model access. [GENERATE.md](GENERATE.md#coding-tool-readiness) explains the distinction.

```sh
python3 scripts/setup.py
python3 scripts/check_environment.py
python3 generator/run.py --target all
python3 scripts/setup.py
python3 scripts/verify.py --suite all
python3 scripts/verify.py --suite harness
python3 scripts/regenerate_check.py
```

Select an individual target with --target python or --target typescript. Candidate failures preserve published clients. A target-only run without the other client explicitly reports interoperability NOT_RUN. Reports and nonzero failure/blocker exits are part of the contract. Exact interfaces, timeouts, isolation, lock generation, and publication rules are in [GENERATE.md](GENERATE.md).

## Desktop prerequisites (Ubuntu / WSL)

Before setup, install the native packages using your own terminal; sudo may ask for your password:

```sh
sudo apt-get update
sudo apt-get install -y python3-tk xvfb x11-xkb-utils x11-utils
```

`python3-tk` supplies the desktop runtime and Tcl/Tk dependencies. `xvfb` provides an isolated display for automated GUI checks; `x11-xkb-utils` supplies its keyboard compiler, and `x11-utils` supplies the window inspection tool used by the launch test. Setup checks these prerequisites and reports BLOCKED if unavailable; it does not run sudo or ask for your password. No pip dependency is needed.

An interactive desktop/X display is required to see the Python GUI (for example, working WSLg on a supported Windows/WSL installation). Automated tests use Xvfb and do not need a visible desktop. Verify Tk with `python3 -m tkinter`; a small test window should appear. If that fails, resolve the Tk/display diagnostic before launching the application. `--machine`, `--help`, and stopped-store reset remain usable without a display. Native Windows/macOS are unverified.

## Run the local demonstration

Open a terminal in this project directory and run:

```sh
python3 scripts/setup.py
python3 scripts/build.py --target all
python3 scripts/demo.py --port 8765
```

Keep that terminal open. The demo prints a browser URL and a complete Python command for a second terminal with a fresh store. In VS Code open another terminal with +, use the same project directory, and paste the printed command. In the desktop window enter `alice` and click **Log in**. Open the printed local URL in a fresh private browser window and log in as `bob`. See [the exact launch steps](TESTING.md#manual-launch-two-terminals-and-one-browser).

In Alice's desktop window, set Recipient to `bob`, type `Hi Bob, I have something important to tell you`, and click **Send**. Bob sees it in the browser inbox and replies to `alice` with `What is it?`. Both windows show inbox and outgoing messages, connection status, and queued / accepted by server / failed states. Select a desktop row to read its complete message in the detail pane. Follow [the eight-step offline walkthrough](TESTING.md#manual-interoperability-walkthrough). Development transport controls each client independently; automated tests also fail real API transport while keeping the server alive.

## Operate the server from a desktop window

After installing the [desktop prerequisites](#desktop-prerequisites-ubuntu--wsl), run:

```sh
python3 scripts/setup.py
python3 scripts/build.py --target all
python3 server/gui.py
```

In **Local Messenger - Server**, keep port `8765` and the default browser assets directory, then click **Start**. The window shows **Running**, the listening URL, a session ID, response/error counts, and accepted-message activity. Click **Open browser** to open the URL; use a fresh private browser context and log in as `bob`. Start the Python client in another terminal with a fresh store:

```sh
python3 generated/python-client/main.py --server http://127.0.0.1:8765 --state-dir "$(mktemp -d)"
```

Log in as `alice` and exchange messages. If you selected a different server port, use the URL shown in the server window. Select an accepted-message row to read its complete text. Counts represent server acceptance and HTTP responses, not delivery/read receipts or online users.

Use **Stop** or close the window to stop its server. Every **Start** begins an empty server session; use fresh/reset client stores and a fresh private browser context after restarting. Keep the server running during client-offline tests. The existing terminal demo remains available. Follow [the server GUI walkthrough](TESTING.md#server-gui-manual-verification-chg-002) for detailed checks.

## How to request changes

[FUTURE.md](FUTURE.md) holds active requests. Add a real request there with a unique CHG ID, desired change, expected result, scope, behavior to preserve, and optional reason/priority. Its field examples are instructional only. Saving the file does not execute it.

For review without implementation:

```text
Review the active requests in FUTURE.md. Explain scope, conflicts, order,
and test impact. Do not apply requests or change code.
```

For a selected request you actually added (replace the placeholder):

```text
Apply only <selected request IDs> from FUTURE.md. Update affected source
decisions, specifications, and independent tests before regenerating clients.
Verify the intended change and clean regeneration. Archive original wording,
changed source values, and actual evidence in docs/CHANGES.md before removing
only completed selected entries. Preserve unrelated and incomplete requests.
```

Examples are not an active queue. Documentation-only requests use document checks; an authorized code change uses relevant application checks and regeneration. Evolution results are recorded only after an actual change passes the generic harness and clean regeneration. Do not automatically reuse any previous project's feature experiment.

## Limits, authorship, and release

Runtime is local and unauthenticated; sender names are not secure identities. Client persistence does not provide server crash recovery. Keep one server session alive during outage testing, use fresh/reset client stores after restarting the server, and do not expect offline browser asset loading or closed-app delivery. One active instance per identity is supported. These limits and deferred coverage are specified in PRODUCT/ACCEPTANCE and TESTING.

The user provided direction and the construction guide. The parent coding agent authored specifications and retained infrastructure/tests; actual isolated Codex harness calls authored both clients. The Python client was regenerated for the maximum-size response regression and later for CHG-001 desktop presentation. The completed change and full verification history are archived in [docs/CHANGES.md](docs/CHANGES.md). Retained does not mean human-authored. Actual run counts, hashes, and limitations are recorded in STATUS. See [authorship](DESIGN.md#authorship-and-regeneration-ownership), [source provenance](docs/ASSIGNMENT.md), and [review mapping](docs/ASSIGNMENT_REVIEW.md).

Authentic incremental commits record the implementation and generation milestones. `python3 scripts/package.py` packages committed source plus a Git bundle, verifies source inventory, and checks history restoration in a fresh clone. It requires a clean working tree. A review archive can be prepared with pending human observations; final readiness must report those outstanding checks honestly. Never include credentials, live client stores, caches, or previous generation transcripts in the source archive.
