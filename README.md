# Reusable Spec-Driven Code Generator

A reusable agentic harness that turns written specifications into independent Python and TypeScript clients. A local messaging application provides a concrete example of offline queues, durable client state, and interoperability.

**Status: Stage 2 implementation complete.** The expanded 44-test acceptance suite and nine harness guard tests pass. Clean regeneration and archive/history restoration are verified; user manual review is pending. [Status and evidence](docs/STATUS.md) records actual runs and limitations.

## Start here

To try the committed application, follow the local demonstration below and [TESTING.md](TESTING.md). Read [the resolved choices](docs/DECISIONS.md) and the edit map if you want to change behavior. Leave preference cells blank when the defaults fit; you do not need to author wire protocols or database schemas.

The defaults are a Python terminal client, a plain TypeScript browser client, a small local Python server, and Codex-driven generation. Both clients persist identity and messages. The server retains data only while its process runs; each new server session requires explicit fresh/reset demo client stores. No extra feature or evolution experiment is active.

To bootstrap a separate new project, begin with the canonical [Instruction_for_Agent.md](Instruction_for_Agent.md). This README is the resulting operating guide; it is not a second construction template or preference form. Reading Markdown does not execute a workflow.

## What you can edit

Edit the `Your input` or `Your observation` cells inside the paired USER markers. Keep field IDs and examples. Blank, whitespace-only, TBD, and — preferences select adjacent defaults. Explicit false, 0, and none are real choices and may need compatibility reconciliation. Blank observations are missing facts, never successful example results.

| File | Section key / fields | What you write | Adjacent example |
|---|---|---|---|
| [specs/PRODUCT.md](specs/PRODUCT.md#your-product-choices) | PRODUCT_CHOICES / P01–P11 | Desired product, interfaces, scope, and visible behavior | P04: Python CLI and TypeScript desktop browser |
| [specs/ACCEPTANCE.md](specs/ACCEPTANCE.md#your-acceptance-expectations) | ACCEPTANCE_CHOICES / A01–A05 | Expected scenarios and outcomes | A02: lost acknowledgment still produces one inbox entry |
| [DESIGN.md](DESIGN.md#your-design-priorities) | DESIGN_CHOICES / D01–D05 | Priorities and tradeoffs | D01: offline correctness and regeneration before polish |
| [AGENTS.md](AGENTS.md#your-working-preferences) | WORKFLOW_CHOICES / W01–W05 | Tool and working preferences | W01: Codex; another supported choice is Claude Code |
| [TESTING.md](TESTING.md#your-manual-observations) | MANUAL_OBSERVATIONS / M01–M06 | Actual observations after personally testing Stage 2 | M03: the observed offline scenario result; blank means NOT_RUN |

All 26 preference cells and six observation cells are initially blank. Effective defaults are recorded separately in docs/DECISIONS.md. The agent maintains the technical portions of these documents, PROTOCOL/PYTHON/TYPESCRIPT, generation instructions, status, and traceability. Changes to preferences are reconciled across those documents before implementation. The user does not need to edit wire schemas or generated source to request different behavior.

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
| FUTURE.md / docs/CHANGES.md | User's active requests / completed request evidence; both histories start empty |
| specs/PRODUCT.md, PROTOCOL.md, ACCEPTANCE.md | Shared intent, wire behavior, and independent acceptance contract |
| specs/PYTHON.md / TYPESCRIPT.md | Platform-specific interfaces, storage, and lifecycle |
| docs/DECISIONS.md / STATUS.md | Effective choices, provenance, readiness and actual evidence |
| docs/ASSIGNMENT.md / ASSIGNMENT_REVIEW.md | Neutral requirements-source summary and criterion-to-evidence mapping |
| generator/ | Retained generic orchestration, configuration, prompts, and tool adapter |
| server/ | Retained small local server |
| tests/ | Retained independent tests and fault fixtures |
| scripts/ | Retained environment/setup/build/test/demo/proof/package commands |
| generated/python-client/ | **Generated deletion boundary** for Python source and target declarations |
| generated/typescript-web/ | **Generated deletion boundary** for browser source and target declarations |
| artifacts/ | Disposable generation/build/test reports, candidates, and caches; excluded from source publication |

Do not delete the server, tests, scripts, specs, or harness when checking regeneration. Source must be recreated through the coding tool; restoring previous clients from Git or an archive does not prove generation. The clean proof uses a separate retained-input workspace and preserves your current tree.

## Setup, generation, and verification

Verified environment: Ubuntu 22.04/WSL2, Python 3.10.12, Node 22.17.0, npm 10.9.2, and Chromium 141.0.7390.37. Setup installs exact TypeScript/Playwright and project-local Codex 0.166.0 dependencies from real npm locks. It can extract missing Ubuntu NSS/NSPR browser libraries into /tmp/reusable-spec-native without system installation. Other operating systems are unverified.

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

## Run the local demonstration

Open a terminal in this project directory and run:

```sh
python3 scripts/setup.py
python3 scripts/build.py --target all
python3 scripts/demo.py --port 8765
```

Keep that terminal open. The demo prints a browser URL and a complete Python command for a second terminal with a fresh store. In VS Code open another terminal with +, use the same project directory, paste the printed Python command, and enter alice at the client's Username prompt. Open the printed local URL in a fresh private browser window and enter bob. See [the exact launch steps](TESTING.md#manual-launch-two-terminals-and-one-browser).

Alice types `send bob Hi Bob, I have something important to tell you` at the running client's prompt. Bob sees it in the browser inbox and replies to alice with `What is it?`. CLI commands inbox/outbox/status and browser rows show messages and queued/accepted by server/failed states. Follow [the eight-step offline walkthrough](TESTING.md#manual-interoperability-walkthrough), including the final Alice reconnect. Manual development toggles control each client independently; automated tests additionally fail real API transport without shutting down the server.

## How to request changes

[FUTURE.md](FUTURE.md) starts with no active requests. Add a real request there with a unique CHG ID, desired change, expected result, scope, behavior to preserve, and optional reason/priority. Its field examples are instructional only. Saving the file does not execute it.

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

Examples are not an active queue. Documentation-only requests use document checks; an authorized code change uses relevant application checks and regeneration. Evolution execution remains NOT_RUN until an actual change or explicitly requested isolated experiment is verified with the generic harness. Do not automatically reuse any previous project's feature experiment.

## Limits, authorship, and release

Runtime is local and unauthenticated; sender names are not secure identities. Client persistence does not provide server crash recovery. Keep one server session alive during outage testing, use fresh/reset client stores after restarting the server, and do not expect offline browser asset loading or closed-app delivery. One active instance per identity is supported. These limits and deferred coverage are specified in PRODUCT/ACCEPTANCE and TESTING.

The user provided direction and the construction guide. The parent coding agent authored specifications and retained infrastructure/tests; actual isolated Codex harness calls authored both clients. The Python client was regenerated after a valid maximum-size response regression was reproduced. Retained does not mean human-authored. Actual run counts, hashes, and limitations are recorded in STATUS. See [authorship](DESIGN.md#authorship-and-regeneration-ownership), [source provenance](docs/ASSIGNMENT.md), and [review mapping](docs/ASSIGNMENT_REVIEW.md).

Authentic incremental commits record the implementation and generation milestones. `python3 scripts/package.py` packages committed source plus a Git bundle, verifies source inventory, and checks history restoration in a fresh clone. It requires a clean working tree. A review archive can be prepared with pending human observations; final readiness must report those outstanding checks honestly. Never include credentials, live client stores, caches, or previous generation transcripts in the source archive.
