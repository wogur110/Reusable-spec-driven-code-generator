# Jaehyeok-spec-driven-code-generator

## 1. Project overview

A reusable agentic harness that turns written specifications into independent Python and TypeScript clients. The generator is the main deliverable; a local messaging application demonstrates offline queues, durable client state, and interoperability.

- **[Section 2: Regenerate the clients](#2-regenerate-the-clients)** — prerequisites, commands, and the exact generated-code boundaries.
- **[Section 7: Run and test the application](#7-run-and-test-the-application)** — launch the Python and browser clients, use the server GUI, and run automated checks.

**Latest recorded verification:** completed CHG-001–004 behavior, 92 passing acceptance tests, nine passing harness guards, and a passing independent clean-regeneration proof. [Section 3](#3-verify-clean-regeneration) explains the proof and links actual evidence.

## 2. Regenerate the clients

Regeneration recreates the behavior defined by the current registered specifications, including completed CHG-001–004. Pending requests in FUTURE.md are excluded.

For unchanged, already reconciled specifications, use the commands below. If you edited USER choices such as PRODUCT.md, first use the [default regeneration instruction](#default-regeneration-instruction) in section 8 so the agent reconciles the specifications and tests. The shell harness does not perform that reconciliation itself.

The generated replacement boundaries are **`generated/python-client/`** and **`generated/typescript-web/`**. Keep the rest of the repository: specifications, documentation, generator, server, scripts, tests, and dependency manifests/locks. Deletion is optional; the harness creates fresh candidates either way.

### Environment and coding-tool access

Verified environment: Ubuntu 22.04/WSL2, Python 3.10.12, Node 22.17.0, npm 10.9.2, and Chromium 141.0.7390.37. Setup installs exact TypeScript/Playwright and project-local Codex 0.166.0 dependencies from real npm locks. It can extract missing Ubuntu NSS/NSPR browser libraries into /tmp/reusable-spec-native without system installation. Other operating systems are unverified.

Install the desktop prerequisites below before running setup. Run all commands from the project root, the directory containing this README.

Generation uses requested model gpt-6-astra, successfully checked with the current account; the service did not report an effective model identifier. Each harness run repeats a bounded authenticated preflight. After `scripts/setup.py` installs the local CLI, authenticate it if needed with `generator/codex/node_modules/.bin/codex login` before running generation. Running committed clients requires no model access. [GENERATE.md](GENERATE.md#coding-tool-readiness) explains the distinction.

### Desktop prerequisites (Ubuntu / WSL)

Before setup, install the native packages using your own terminal; sudo may ask for your password:

```sh
sudo apt-get update
sudo apt-get install -y python3-tk xvfb x11-xkb-utils x11-utils
```

`python3-tk` supplies the desktop runtime and Tcl/Tk dependencies. `xvfb` provides an isolated display for automated GUI checks; `x11-xkb-utils` supplies its keyboard compiler, and `x11-utils` supplies the window inspection tool used by the launch test. Setup checks these prerequisites and reports BLOCKED if unavailable; it does not run sudo or ask for your password. No pip dependency is needed.

An interactive desktop/X display is required to see the Python GUI (for example, working WSLg on a supported Windows/WSL installation). Automated tests use Xvfb and do not need a visible desktop. Verify Tk with `python3 -m tkinter`; a small test window should appear. If that fails, resolve the Tk/display diagnostic before launching the application. `--machine`, `--help`, and stopped-store reset remain usable without a display. Native Windows/macOS are unverified.

### Recreate both clients in this repository

Run these commands one at a time from the project root, the folder containing this README. If you edited USER choices, complete the reconciliation in [the default workflow](#default-regeneration-instruction) first. Stop running demo clients/server, and finish any source or specification edits before generation. Keep the retained inputs unchanged while generation runs.

```sh
python3 scripts/setup.py
python3 scripts/check_environment.py --generation
python3 generator/run.py --target all
python3 scripts/setup.py --skip-browser-install
python3 scripts/build.py --target all
python3 scripts/verify.py --suite all
```

Use this sequence whether the client directories still exist or have already been deleted. No deletion is necessary: the harness starts isolated candidates without the selected targets' old source, validates them, and replaces the published directories only after checks pass. Existing published source is preserved on failure; if you already deleted it, a failed run leaves it absent. Stop at a failed command and inspect its report rather than treating partial output as a working application.

The first setup installs retained tools and matching Chromium even when both clients are absent. The post-generation setup/build installs the newly published client dependencies and recreates disposable browser assets, which are not included in source publication. The harness itself already checks candidates before publication; the final verify command confirms the published checkout. Successful current full verification reports **PASS 92 tests**. Launch afterward using [the local demonstration](#run-the-local-demonstration) or [the server GUI](#operate-the-server-from-a-desktop-window); a new server session needs fresh/reset client stores.

For only one client, replace the generation command above with one of:

```sh
python3 generator/run.py --target python
python3 generator/run.py --target typescript
```

Choose one command for the target you need. Full interoperability is checked when the other client is present; otherwise a single-target run reports interoperability NOT_RUN. Use `--target all` when both clients are missing. If only `generated/typescript-web/dist/` is missing and its source remains, run `python3 scripts/build.py --target typescript` after dependency setup; no model generation is needed.

### What must remain

Keep the repository outside the two generated client directories, including:

| Retained inputs | Why they are needed |
|---|---|
| Root Markdown, specs/ and docs/ | Behavior, UI/storage/protocol contracts, decisions and workflow context; keep DIRECTORY.md and PRESENCE.md registered in targets.json. |
| generator/ | Runner, configuration, generic prompt, and coding-tool package manifests/locks. |
| server/ | Existing server implementation and GUI used by validation; the current harness regenerates clients only. |
| tests/ and scripts/ | Independent acceptance checks, fault fixtures, setup/build/demo and clean-proof commands. |
| Retained package.json/package-lock.json files | Reinstall pinned test and coding-tool dependencies; generated client manifests and managed locks are recreated during generation/setup. |

Markdown plus the generator folder alone is insufficient for the current workflow: the retained server, tests and scripts are also required. Their code is not recreated by `--target all`. The two replacement boundaries are `generated/python-client/` and `generated/typescript-web/`. Deleting a generated helper file is recovered by regenerating its entire target; do not rely on the generator to preserve hand edits there.

The machine also needs Python/Node/npm, the native desktop prerequisites above, package/browser downloads when dependencies are missing, and access to the configured authenticated coding tool/model. Credentials stay outside the repository. The actual harness preflight checks model access; a version or environment check alone does not establish it.

## 3. Verify clean regeneration

### Prove reconstruction without deleting your working copies

After setup and coding-tool authentication, run:

```sh
python3 scripts/regenerate_check.py
```

This creates a separate retained-input workspace with no prior client source, regenerates both clients through the real harness, builds them, and runs acceptance inside the harness and again standalone. It preserves this repository's published clients and stores; its fresh clients remain in the disposable workspace rather than replacing your working copies. Expect a substantial run: actual model calls, builds, tests and bounded repairs are involved. This proof is separate from ordinary `--suite all`, which never invokes generation.

Reports are written to `artifacts/generation/<run-id>/report.json` and `artifacts/regeneration/<run-id>/report.json`. Read the final PASS/FAIL/BLOCKED status, publication result, collected/passed counts and repair history. Authentication/model or dependency failures need their reported cause resolved before a new run. A failed candidate is not permission to weaken retained tests or manually patch published clients; put intended behavior in the specifications and follow the harness workflow.

Run the separate harness guard checks as well:

```sh
python3 scripts/verify.py --suite harness
```

The current guard suite contains nine tests. It checks orchestration safeguards using controlled fixtures; the clean proof above performs actual coding-tool generation.

### Recorded results

**Both deleted client directories were recreated from the reconciled specifications.** Published run `20261102T002927228257Z` passed 92 acceptance tests after two bounded repair rounds. Independent clean proof `20261102T010021541172Z` began without previous client source, Git objects or old transcripts; both fresh clients passed all 92 cases inside the harness and again standalone, on their initial generation calls. This demonstrates tested behavioral reconstruction; future model calls may still require bounded repairs. See [the recorded results](docs/STATUS.md#p01-reconciliation-and-client-regeneration).

Published-checkout verification also passed 92/92, and harness guards passed 9/9. Reports record exact tested input hashes; later documentation edits do not rewrite those snapshots. See [STATUS](docs/STATUS.md#p01-reconciliation-and-client-regeneration) and [EVIDENCE.json](docs/EVIDENCE.json).

The intended result is equivalent specified behavior and comparable UI structure. Generated filenames, internal code, exact spacing, fonts and other unspecified styling can differ. Current tests check messaging, persistence, presence, controls and browser layout geometry; they do not compare every screen pixel. Regeneration recreates application code, not lost client messages or in-memory server data. Restore a saved Git revision or source archive when you need the exact original source bytes.

## 4. How this project was created

The user supplied direction, the construction guide, product choices, change requests, and review feedback. The project was built in stages:

1. **Construction guide:** [Instruction_for_Agent.md](Instruction_for_Agent.md) defined the required documents, ownership boundaries, workflow, and verification obligations.
2. **Stage 1 — Markdown specifications:** the parent coding agent authored product, protocol, platform, acceptance, design, and workflow documents, with editable USER tables. Effective choices and their provenance were recorded in [DECISIONS](docs/DECISIONS.md).
3. **User review:** preferences were reviewed and later changes reconciled into authoritative specifications. Blank inputs selected documented defaults; they were not filled with agent-authored answers.
4. **Stage 2 — retained infrastructure and generated clients:** the parent agent implemented the server, independent tests, scripts, and reusable harness. The harness invoked isolated Codex coding agents to create Python and TypeScript clients from their registered specifications.
5. **Verification and evolution:** candidates were built and tested before publication, followed by independent clean regeneration. Completed CHG-001–004 updated the contracts and affected implementations. The later P01 name change was reconciled before regenerating both clients again. The user recorded manual observations separately.

Retained infrastructure is also agent-authored; retained does not mean hand-written by the user. Generated client source is committed, while the harness can replace its declared directories. See [authorship and ownership](DESIGN.md#authorship-and-regeneration-ownership), [completed change history](docs/CHANGES.md), and [requirements traceability](docs/ASSIGNMENT.md).

### Stages and copy-ready instructions

For a separate new project, begin with the construction guide's [Stage 1 instruction](Instruction_for_Agent.md#stage-1-instruction-the-user-can-send), then review the Markdown and use its [Stage 2 instruction](Instruction_for_Agent.md#stage-2-instruction-the-user-can-send). Stage 1 creates specifications and stops before implementation; Stage 2 requires a separate request. These are messages to the coding agent, not shell commands.

For this completed checkout, use [regeneration](#2-regenerate-the-clients) or the [change-request workflow](#how-to-request-changes). Reading or editing Markdown alone starts no generation.

## 5. How the harness works

The entry point is [generator/run.py](generator/run.py), configured by [generator/targets.json](generator/targets.json) and the [generic client prompt](generator/prompts/client.md).

1. Select shared product/protocol/acceptance specifications, the target's platform specification, and registered DIRECTORY/PRESENCE extensions.
2. Freeze retained inputs and check authenticated coding-tool access. Each target gets an isolated candidate workspace without previous client source, Git history, or the other client's implementation.
3. Invoke the coding tool, build the candidates, and run independent retained checks. Both-target generation requires interoperability before publication.
4. On failure, supply relevant diagnostics for up to three bounded repair rounds. Repairs cannot change frozen specifications, retained tests, or assertions.
5. Publish validated source into the declared generated directories, with rollback protection, and record actual inputs, tool/model details, attempts, and results.

Shared written contracts constrain both implementations; the clients do not share messaging source. The retained server is outside the client generation boundary. [GENERATE.md](GENERATE.md) defines the complete isolation, timeout, integrity, and publication rules; [DESIGN.md](DESIGN.md) explains the tradeoffs.

## 6. Repository map and ownership

The implementation paths below exist. Only the two generated client directories are replacement boundaries.

| Location | Role / regeneration ownership |
|---|---|
| Instruction_for_Agent.md | Retained construction process and field catalog |
| README.md, AGENTS.md, DESIGN.md, GENERATE.md, TESTING.md | Retained navigation, agent rules, rationale, generation and test contracts |
| FUTURE.md / docs/CHANGES.md | User's active requests / completed request evidence; archive completed requests with actual evidence |
| specs/PRODUCT.md, PROTOCOL.md, ACCEPTANCE.md | Shared intent, wire behavior, and independent acceptance contract |
| specs/SERVER.md | Retained server desktop controls, monitoring, and session lifecycle |
| specs/PYTHON.md / TYPESCRIPT.md | Platform-specific interfaces, storage, and lifecycle |
| specs/DIRECTORY.md / PRESENCE.md | Registered shared extensions for recipient discovery, durable receipts, and explicit Online/Offline notifications |
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

## 7. Run and test the application

Running the generated clients and ordinary acceptance tests requires no coding-tool authentication. Install the [desktop prerequisites](#desktop-prerequisites-ubuntu--wsl) if needed, then choose either the terminal demo or the server GUI below. Both launch the same local server; use one at a time on a given port. If client source is missing, follow [section 2](#2-regenerate-the-clients) first.

### Run the local demonstration

Open a terminal in this project directory and run:

```sh
python3 scripts/setup.py
python3 scripts/build.py --target all
python3 scripts/demo.py --port 8765
```

Keep that terminal open. The demo prints a browser URL and a complete Python command for a second terminal with a fresh store. In VS Code open another terminal with +, use the same project directory, and paste the printed command. In the desktop window enter `alice` and click **Log in**. Open the printed local URL in a fresh private browser window and log in as `bob`. See [the exact launch steps](TESTING.md#manual-launch-two-terminals-and-one-browser).

In Alice's desktop window, set Recipient to `bob`, type `Hi Bob, I have something important to tell you`, and click **Send**. Bob sees it in the browser inbox and replies to `alice` with `What is it?`. Both windows show inbox and outgoing messages, connection status, and queued / accepted by server / failed states. Select a desktop row to read its complete message in the detail pane. Follow [the eight-step offline walkthrough](TESTING.md#manual-interoperability-walkthrough). Development transport controls each client independently; automated tests also fail real API transport while keeping the server alive.

### Operate the server from a desktop window

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

### Run automated tests

After setup, run from the project root:

```sh
python3 scripts/verify.py --suite all
python3 scripts/verify.py --suite harness
```

The current baseline expects **92 acceptance cases** and **nine harness guards**, with no failed or skipped required cases. The acceptance command builds the clients and exercises protocol, headless Python, real desktop, and browser behavior. It does not invoke generation; use [section 3](#3-verify-clean-regeneration) for that proof.

For manual verification, follow the [offline interoperability and restart walkthrough](TESTING.md#manual-interoperability-walkthrough), then check [explicit Online/Offline notifications and web layout](TESTING.md#chg-004-web-layout-and-explicit-presence). Record your actual observations in TESTING.md; automated reports do not fill the user fields.

## 8. Customize specifications and regenerate

### What you can edit

Edit the `Your input` or `Your observation` cells inside the paired USER markers. Keep field IDs and examples. Blank, whitespace-only, TBD, and — preferences select adjacent defaults. Explicit false, 0, and none are real choices and may need compatibility reconciliation. Blank observations are missing facts, never successful example results.

| File | Section key / fields | What you write | Adjacent example |
|---|---|---|---|
| [specs/PRODUCT.md](specs/PRODUCT.md#your-product-choices) | PRODUCT_CHOICES / P01–P11 | Desired product, interfaces, scope, and visible behavior | P04: Python desktop GUI and compact TypeScript browser; P10: completed directory/receipt/presence features |
| [specs/ACCEPTANCE.md](specs/ACCEPTANCE.md#your-acceptance-expectations) | ACCEPTANCE_CHOICES / A01–A05 | Expected scenarios and outcomes | A02: lost acknowledgment still produces one inbox entry |
| [DESIGN.md](DESIGN.md#your-design-priorities) | DESIGN_CHOICES / D01–D05 | Priorities and tradeoffs | D01: offline correctness and regeneration before polish |
| [AGENTS.md](AGENTS.md#your-working-preferences) | WORKFLOW_CHOICES / W01–W05 | Tool and working preferences | W01: Codex; another supported choice is Claude Code |
| [TESTING.md](TESTING.md#your-manual-observations) | MANUAL_OBSERVATIONS / M01–M06 | Actual observations after personally testing Stage 2 | M03: the observed offline scenario result; blank means NOT_RUN |

P01 explicitly names the project `Jaehyeok-spec-driven-code-generator`; the other 25 preference inputs remain blank. The user recorded M01–M05, including PASS for offline/restart checks and Good for usability; M06 remains blank. Adjacent defaults describe the reconciled baseline, with previous values and provenance in [docs/DECISIONS.md](docs/DECISIONS.md). Unchanged blanks preserve completed features. The agent maintains technical contracts and workflow/evidence sections. A regeneration request checks and reconciles changed preferences by default; use [the default regeneration instruction](#default-regeneration-instruction).

### Default regeneration instruction

**Every request to regenerate defaults to checking your current USER choices first.** The agent compares the preference cells in [the edit map](#what-you-can-edit) with the last reconciled decision snapshot. Changed choices are reconciled into the specifications, independent tests, and any necessary retained implementation/configuration before generation. If no choices changed, the existing reconciled contract is used unchanged.

Completed behavior through **CHG-004** remains unless your changed choices intentionally supersede it. Unchanged blank cells do not undo completed features. After another update is completed, its reconciled specifications become the new baseline. FUTURE.md remains excluded unless you separately request applying a pending change.

1. Optionally edit `Your input` cells in [specs/PRODUCT.md](specs/PRODUCT.md#your-product-choices) or the other preference forms. Keep field IDs and examples.
2. Send the instruction below to your coding agent. It works whether or not you edited preferences.
3. After successful generation and verification, follow [TESTING.md](TESTING.md) to check the application manually.

```text
Regenerate both clients using the default workflow in README.md.
Read Instruction_for_Agent.md, AGENTS.md, the current registered specifications,
and the USER preference forms listed in the README edit map.
Compare current preference cells with the last reconciled decision snapshot
and preserve my exact wording. If choices changed, record previous/new values
and reconcile docs/DECISIONS.md, affected specifications, independent retained
tests, and necessary retained implementation/configuration before generation.
Synchronize affected default/example columns with the intended contract and
record previous/new wording. Keep unverified changes clearly labeled.
If no choices changed, use the current reconciled contract unchanged.
Preserve completed behavior through CHG-004 and any later completed updates,
except where my changed choices intentionally supersede it. Unchanged blank
cells must not reset completed features to the original defaults.
Do not apply FUTURE.md, replay docs/CHANGES.md as requirements, or restart Stage 1.
Resolve genuine requirement conflicts before proceeding with dependent work.
Freeze the reconciled inputs, regenerate both clients through the existing
harness, and run the required checks and clean-regeneration proof.
Update operating documentation and evidence with actual results and blockers.
Preserve my manual observation fields; do not fill them with automated results.
```

This is an instruction to the coding agent. Saving preference cells alone does not start work. `generator/run.py` reads PRODUCT.md and the other registered inputs, but does not reconcile preferences or rewrite retained specifications, tests, or server code itself. The parent agent performs any reconciliation before freezing inputs; candidate-generation and repair agents must keep those inputs unchanged. Manual observation cells in TESTING.md record facts and are not generation choices.

### Which updates regeneration includes

Regeneration reproduces the **current registered specifications in this checkout**, including completed updates through **CHG-004**. That includes the Python desktop, retained server GUI compatibility, shared directory/receipt behavior, compact web layout, and explicit Offline/Online notifications. It does not return to the original Stage 1 defaults.

`generator/targets.json` selects PRODUCT.md, PROTOCOL.md, ACCEPTANCE.md, the platform specification, and the registered DIRECTORY.md/PRESENCE.md extensions. Completed changes have already been incorporated into these authoritative contracts; the generator does not replay change-history entries to discover features.

**FUTURE.md is a pending-request queue, not a generation specification.** It is absent from the configured coding-agent inputs. The trusted verifier/clean-proof workspace may retain it for repository integrity, but it is not supplied to target-generation agents. Adding a request there does not change regenerated behavior. A pending request must be explicitly applied, reconciled into the registered specifications and tests, and verified in a separate change workflow first.

### When to add more specification detail

The current retained inputs are sufficient for the tested CHG-004 behavior. For tighter similarity to a particular UI, add an explicitly registered UI specification with exact component positions, dimensions, spacing, colors, fonts, column sizing, selection/focus styling, and empty/error/offline states for both platforms. Pair it with retained screenshot comparisons using fixed viewports, deterministic sample data, fonts and platform/theme settings. Keep those references outside the generated deletion boundaries, and register any new specification in `generator/targets.json`. These stricter visual checks are recommendations, not implemented guarantees.

Pinned dependencies, recorded tool/model choices and run fingerprints already help repeatability. They cannot guarantee identical model output. Any additional behavior you want preserved must become an authoritative requirement and an independent acceptance check before regeneration. Exact source recovery remains a Git/archive operation.

## 9. Completed changes and future development

### Change summary

- **CHG-001:** Replaced the Python terminal interface with a desktop GUI, preserved existing stored data and the headless interface, and added GUI tests and setup instructions. Automated verification and clean regeneration passed.
- **CHG-002:** Added a desktop window to start, stop, and monitor the local server, with session status, message activity, and GUI integration tests. Automated verification and clean regeneration passed.
- **CHG-003:** Adds shared recipient discovery, click-to-address, and per-user server activity with durable receipt acknowledgments. The server shows Online/Offline status; CHG-004 adds explicit mode notifications with heartbeat timeout as fallback. Offline client queues remain unknown to the server. See [manual verification](TESTING.md#shared-directory-and-user-activity-chg-003).
- **CHG-004:** A compact web layout matching the Python workflow, plus explicit client Offline/Online notifications to update server status without peer message traffic. See [manual verification](TESTING.md#chg-004-web-layout-and-explicit-presence).

See [docs/CHANGES.md](docs/CHANGES.md) for the full change history and verification evidence.

### How to request changes

[FUTURE.md](FUTURE.md) holds active requests. Add a real request there with a unique CHG ID, desired change, expected result, scope, behavior to preserve, and optional reason/priority. Its field examples are instructional only. Saving the file does not execute it.

Every authorized development change includes updating affected code, specification sheets, tests, operating docs and preference-table **Example / automatic default** columns. The agent preserves your input/observation cells, records previous/new defaults in DECISIONS, and checks that everything describes the finished behavior before declaring completion. Unaffected defaults stay unchanged; pending requests are not current defaults. This also applies to direct feature or bug-fix requests outside the queue. See [the agent completion rule](AGENTS.md#future-development-completion-rule).

For review without implementation:

```text
Review the active requests in FUTURE.md. Explain scope, conflicts, order,
and test impact. Do not apply requests or change code.
```

For a selected request you actually added (replace the placeholder):

```text
Apply only <selected request IDs> from FUTURE.md. Update affected source
decisions, specification sheets, independent tests, and preference-table
default/example columns before freezing inputs and regenerating affected clients.
Preserve my input and observation cells; record previous/new defaults and why
they changed. Update code and operating docs, verify the intended behavior and
clean regeneration, and check that specs/docs/defaults match the finished result.
Archive original wording, changed source values/defaults, and actual evidence
in docs/CHANGES.md before removing only completed selected entries.
Preserve unrelated and incomplete requests; keep unverified work clearly labeled.
```

Examples are not an active queue. Documentation-only requests use document checks; an authorized code change uses relevant application checks and regeneration. Evolution results are recorded only after an actual change passes the generic harness and clean regeneration. Do not automatically reuse any previous project's feature experiment.

## 10. Limitations and release packaging

Runtime is local and unauthenticated; sender names are not secure identities. Client persistence does not provide server crash recovery. Keep one server session alive during outage testing, use fresh/reset client stores after restarting the server, and do not expect offline browser asset loading or closed-app delivery. One active instance per identity is supported. These limits and deferred coverage are specified in PRODUCT/ACCEPTANCE and TESTING.

Authentic incremental commits record the implementation and generation milestones. `python3 scripts/package.py` packages committed source plus a Git bundle, verifies source inventory, and checks history restoration in a fresh clone. It requires a clean working tree. A review archive can be prepared with pending human observations; final readiness must report those outstanding checks honestly. Never include credentials, live client stores, caches, or previous generation transcripts in the source archive.

The verified automated environment is Ubuntu/WSL; native Windows and macOS remain unverified. User-reported offline and restart checks passed, with usability recorded as Good. Exact browser/version, tested revision, M06 evidence, and packaging of the current revision remain outstanding; [STATUS](docs/STATUS.md) distinguishes these from completed automated verification.
