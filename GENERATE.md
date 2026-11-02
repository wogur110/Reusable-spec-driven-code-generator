# Generation harness contract

Status: CHG-001–004 generation/evolution complete. The last CHG-004 snapshot passed 92 acceptance tests in the harness and again standalone, plus nine harness guards. [STATUS](docs/STATUS.md) records actual runs and failures; documentation-only reconciliation does not create new runtime evidence. Application behavior lives in registered specs; this document defines reusable orchestration.

## Inputs and target configuration

Implement generator/run.py using Python standard-library orchestration. Options: --spec-root specs, --config generator/targets.json, --target all|python|typescript (default all), optional --model and --codex overrides. Paths resolve against the project root. Validate configuration before invoking an agent: version, nonempty targets, declared spec existence, safe relative paths, unique non-overlapping output directories directly under generated/, required-output paths, bounded timeouts/repair rounds, and nonempty argument-vector commands. Reject unknown target or missing registered input as BLOCKED with nonzero exit. Semantic contradictions are reconciled from the decision/spec inventory before execution; do not pretend path validation proves semantic consistency.

The following matches generator/targets.json. The project-local CLI and requested model were selected after a successful authenticated writable preflight on 2026-11-01. Effective model identity was UNREPORTED.

```json
{
  "version": 1,
  "shared_specs": [
    "PRODUCT.md",
    "PROTOCOL.md",
    "ACCEPTANCE.md"
  ],
  "extensions": [
    "DIRECTORY.md",
    "PRESENCE.md"
  ],
  "context_files": [
    "Instruction_for_Agent.md",
    "README.md",
    "AGENTS.md",
    "DESIGN.md",
    "GENERATE.md",
    "TESTING.md",
    "docs/DECISIONS.md"
  ],
  "agent": {
    "tool": "codex",
    "binary": "generator/codex/node_modules/.bin/codex",
    "model": "gpt-6-astra",
    "timeout_seconds": 600,
    "template": "generator/prompts/client.md"
  },
  "repair_rounds": 3,
  "total_timeout_seconds": 5400,
  "dependency_policy": {
    "python": "Python >=3.10 standard library including tkinter/ttk; native Tcl/Tk 8.6; Xvfb for retained GUI tests",
    "node": ">=22",
    "typescript": "5.9.3",
    "playwright": "1.56.1",
    "browser_runtime": "no dependencies or CDN"
  },
  "targets": {
    "python": {
      "specs": [
        "PYTHON.md"
      ],
      "output": "generated/python-client",
      "required_files": [
        "main.py",
        "gui.py"
      ],
      "managed_lockfiles": [],
      "checks": [
        [
          "{python}",
          "scripts/build.py",
          "--target",
          "python"
        ],
        [
          "{python}",
          "scripts/verify.py",
          "--suite",
          "python-interface"
        ]
      ]
    },
    "typescript": {
      "specs": [
        "TYPESCRIPT.md"
      ],
      "output": "generated/typescript-web",
      "required_files": [
        "index.html",
        "styles.css",
        "src/main.ts",
        "package.json",
        "package-lock.json",
        "tsconfig.json"
      ],
      "managed_lockfiles": [
        "package-lock.json"
      ],
      "checks": [
        [
          "{python}",
          "scripts/build.py",
          "--target",
          "typescript"
        ]
      ]
    }
  },
  "setup_command": [
    "{python}",
    "scripts/setup.py",
    "--skip-browser-install"
  ],
  "verify_command": [
    "{python}",
    "scripts/verify.py",
    "--suite",
    "all",
    "--report",
    "{report}"
  ],
  "verify_timeout_seconds": 600
}
```

Use argument arrays without shell interpolation. {python} is the current interpreter; {report} is an owned report path. Freeze config after any authorized readiness reconciliation. Trusted snapshots allow root Markdown/.gitignore, generator/server/tests/scripts/specs/docs, and explicitly registered context/spec paths; private auth/environment/key files and unregistered files are excluded. Guard checks still detect retained-root changes during execution. A valid test report requires passed equal to the positive collected count, with no failures, skips, or flaky results. Config/prompt hashes identify the exact invocation. Only the selected platform specification is passed with shared inputs. An extension is active only when explicitly listed; its documented delta supersedes the stated baseline clauses and no others. Contradictory/undeclared deltas must be resolved before a run. No feature-specific code in the generic runner or prompt.

## Current-contract regeneration scope

Ordinary generation and clean regeneration use the current registered specification inventory, including completed changes already reconciled into it. The present baseline includes CHG-001–004; it is not the initial construction-guide default. The current config passes DIRECTORY.md and PRESENCE.md alongside the shared and selected platform contracts. FUTURE.md and docs/CHANGES.md are not configured target-agent inputs. They may exist in the trusted retained-input snapshot for integrity/evidence purposes; that does not activate pending requests or historical requirements. Do not add them to agent context or infer new features from their links during a regeneration-only task. Applying a pending change requires a separate explicit user request and the change-request workflow before generation.

### Updated USER choices before regeneration

The parent must also follow [the future development completion rule](AGENTS.md#future-development-completion-rule). Any affected preference-table default/example text is reconciled with the intended specs/tests before input freeze, with prior/new wording recorded separately from user input values. After verification, code, specifications, defaults and operating docs must agree on the resulting behavior; failed or pending changes remain explicitly incomplete. The candidate/repair loop cannot update these retained inputs.

By default, every user request to regenerate includes a parent-agent check of the USER preference forms against the last reconciled decision snapshot. If choices changed, the parent preserves their wording, records previous/new choices, updates affected specifications/tests and any necessary retained implementation/configuration, and resolves real conflicts. If none changed, use the existing reconciled contracts and retained implementation unchanged. These deliberate changes precede the frozen generation run; they are not candidate repairs. Current completed behavior remains except where changed choices intentionally supersede it; unchanged blanks do not reset completed features. FUTURE.md stays outside the selected scope. The generator reads registered inputs, including PRODUCT.md, but does not perform this reconciliation or rewrite retained components itself. After reconciliation, generate from the updated contract and verify against its independent tests and clean proof; prior acceptance results do not prove the changed contract. See [the default README instruction](README.md#default-regeneration-instruction).

## Coding-tool readiness

Stage 2 verified Codex 0.166.0 with requested model gpt-6-astra: exit 0, turn.completed, and the requested readiness file created. The global 0.142.5 default gpt-5.5 request failed with model_not_found. Normal CLI-state access required approved execution outside the parent read-only home restriction; the child workspace-write sandbox and enterprise requirements stayed enabled. No account switch or credential copy was needed. The local CLI is pinned in generator/codex/package.json and its real npm lock. Reports are under artifacts/readiness/.

Historical Stage 1 observation on 2026-11-01: global Codex CLI 0.142.5; local `codex exec --help` advertises stdin prompts, --sandbox workspace-write, --ephemeral, --skip-git-repo-check, --json, --color, -C, and --model. Version/help exited 0 with a read-only PATH-alias warning. This is interface evidence only. At that Stage 1 inspection, model access and writable generation were still unverified; the Stage 2 evidence above supersedes that readiness state.

In Stage 2, choose an actually accessible binary/model using the same account/environment as the harness. An installed CLI's configured model is merely a candidate. Perform one minimal noninteractive request in an isolated disposable workspace, require successful completion, and then record binary/version/requested model and any reported effective model. If the service omits its effective ID, record UNREPORTED. If a compatible local CLI installation is necessary, use this project's own development-tool directory and a real exact lock; never copy another project's implementation or credentials. Account or sandbox failures block actual generation, not independent retained implementation work. Do not start an interactive login inside a child run or assume a paid/account entitlement.

Adapter invocation, with the verified model supplied as an argument:

```text
codex exec --sandbox workspace-write --ephemeral --skip-git-repo-check --json --color never -C <candidate-workspace> --model <verified-model> -
```

Send the prompt on stdin and parse stdout JSON-lines; retain sanitized stderr separately. The chosen flags must be checked again against the actual CLI used in Stage 2. [Official noninteractive execution documentation](https://learn.chatgpt.com/docs/non-interactive-mode) describes scripted execution and event output; the [CLI reference](https://learn.chatgpt.com/docs/cli/reference) documents command options. Never resume a prior session, disable enterprise rules, or bypass the sandbox to obtain a passing result.

Required adapter outcome: process exit 0, valid event stream, a completed turn, no failed turn, expected source files, and integrity checks. Completion alone is not application verification. Missing authentication/model access/native prerequisites are BLOCKED; a completed agent with broken code is FAIL and eligible for bounded repair. Keep raw credentials, full environment dumps, auth files, and personal logs out of evidence.

## Isolation and publication

1. Create artifacts/generation/<run-id>/ and a report marked IN_PROGRESS. Capture start time, root revision if present, selected targets, model/tool metadata, input/config/prompt/test hashes, and scope.
2. Snapshot an allowlist of retained source to a trusted verifier workspace. Include instruction/workflow docs, registered specs, generator/server/tests/scripts, and their existing manifests/locks. Exclude generated clients from initial agent contexts, Git objects, node_modules, dist, caches, stores, credentials, and old transcripts. Specs from an alternate --spec-root must actually replace the corresponding inventory; don't silently read the default directory.
3. Give each agent a separate workspace containing only its shared/selected specs and workflow context. Make retained inputs read-only where supported. For repairs, retain only that target's candidate and bounded actual failure diagnostics. A candidate agent must not run another generator, the full construction workflow, or Git mutations.
4. Compare full retained file inventories and hashes after every agent call and trusted check, including additions/removals. Reject symlinks and path escapes in source. Reject all writes outside selected output and explicitly allowed disposable paths. A workspace-write sandbox is not a per-file allowlist; these checks enforce the narrower contract. Also reject source-root retained inputs changed while the run is active.
5. Copy candidates into trusted verification, remove any agent-authored managed lockfiles, and let the actual package manager create locks/install exact declared dependencies. Do not include managed locks in the agent's required authored-output list. Build/typecheck required outputs and run target interface checks.
6. For all targets, require the complete baseline acceptance suite. For one target, combine the other published client only in trusted verification if available, then require interoperability; if absent, report target-only scope and interoperability NOT_RUN. Missing or zero tests cannot pass. The standalone harness suite uses controlled fixtures and must not recursively invoke real generation during baseline verification.
7. On failure, preserve diagnostics, leave published clients untouched, and repair within the same frozen contract. Retained mutations are terminal failures, not something to conceal by restoring files. A deliberate requirement/test change starts a separately recorded run.
8. When required checks and integrity comparisons pass, publish only candidate source/manifests/real locks to selected boundaries via backup-and-replace with rollback if any replacement fails. Never delete the user's published targets first. Retain failed candidates and concise logs under ignored artifacts; exclude builds/stores/cache from publication.

Repair round 0 is initial generation. Allow three subsequent rounds per invocation, not per individual assertion: at most four calls per selected target (eight total for both). A target that already passed may be retained in its isolated candidate workspace while repairing the failing target; recheck joint behavior before publication. No indefinite automatic retry of service/authentication failures.

Disposable integrity exceptions are explicit: trusted checks may create target-local node_modules/, dist/, and __pycache__/, retained Python __pycache__/, and run-owned artifacts/ or var/ paths. Retained test-tool dependencies may be installed in their declared node_modules/ directory. These paths cannot contain substituted retained source, become agent input, or enter published client source. Retained manifests/locks must exist before the input freeze; only declared target managed_lockfiles are created after it by trusted setup. A new top-level source/configuration file or a change to a frozen source/lock is never a disposable-output exception. Agent workspaces permit only the selected target's authored source; dependency installation belongs to the trusted parent.

## Prompt template contract

generator/prompts/client.md exists with configuration-driven substitutions. It must identify selected target/output, complete input inventory, active extensions, authored required outputs, dependency policy, target checks run by the parent, and actual repair diagnostics. State that only selected output is editable and that no old implementation is supplied or to be searched for. Require complete code, independent implementation, normal storage/transport for test interfaces, and truthful check/blocker reporting. Do not embed messaging algorithms, feature names, finished source, or hard-coded messages in generic prompts. Do not ask a candidate to install dependencies or author fake locks; trusted setup owns these steps.

## Execution bounds and reports

| Operation | Limit |
|---|---|
| Model preflight | 120 seconds |
| One coding-agent call | 600 seconds |
| Dependency setup | 600 seconds |
| One target build/interface check | 120 seconds |
| Baseline acceptance subprocess | 600 seconds |
| One messaging observation | 30 seconds, not the full suite duration |
| One harness invocation | 5,400 seconds total, including repair/checks |
| Outer clean-regeneration proof | 7,200 seconds total including setup and standalone verification |

Terminate owned processes on deadline, allow five seconds for graceful exit, then kill remaining owned processes and reap them. Cap child deadlines to remaining outer budget. Tests close their servers, proxies, CLI processes, contexts, and stores on pass or failure; no orphan listeners. Return 0 for the declared successful scope, 1 for failed generation/validation/integrity, 2 for invalid configuration or missing environment prerequisites. A timeout is never a pass.

Report final PASS/FAIL/BLOCKED, times, commands as argument vectors, exits/timeouts, per-target rounds, input/test/config/prompt/source fingerprints, required-file inventory, collected/passed/failed/skipped counts, and publication outcome. Effective model may be UNREPORTED. A report without completed checks remains IN_PROGRESS or NOT_RUN, never PASS. Concise durable evidence summaries belong in docs/STATUS.md and docs/ASSIGNMENT_REVIEW.md; logs and caches belong in ignored artifacts/.

## Clean regeneration and authorized evolution

Implemented proof command: `python3 scripts/regenerate_check.py`. Make a fresh retained-input copy with no generated source or indirect source copies, Git history, previous agent sessions, transcripts, builds, or client stores. Standard installed interpreters/dependency download caches may be reused only if they cannot contain client implementations; record this environment reuse. Assert target directories are absent before generation. Freeze retained manifests, run setup, actual generator --target all, setup/build, and standalone baseline verification. Compare inventories/hashes afterward and preserve the original project. Record all command outcomes; this outer proof is never called by baseline verification itself.

CHG-001 through CHG-004 demonstrate executed evolution; results are recorded in docs/CHANGES.md. For another selected FUTURE request or separately authorized experiment, first define its spec delta, affected targets, intended independent test changes, migration checks, and any retained server support. Freeze that revised contract; run the ordinary harness with registered extensions, baseline checks where applicable, and new checks. Verify generic runner/adapter/prompt hashes are unchanged to demonstrate adaptation from specs/configuration alone. Retain the reproducible delta/evidence. An isolated experiment must leave baseline source and the FUTURE queue unchanged. Do not pre-create an unrequested feature specification.

## CHG-001 desktop inputs

The Python target requires main.py and gui.py and reads PYTHON/PRODUCT/ACCEPTANCE plus both registered extensions. CHG-001 itself left TypeScript and wire behavior unchanged; CHG-003/004 subsequently changed both clients. README/TESTING list native prerequisites; setup checks Tk/Xvfb/xkbcomp/xwininfo. GUI-01–06 belong to current acceptance and clean proof. Generic orchestration and prompt remain unchanged. Preserve frozen assertions across repairs; DECISIONS records current defaults and original choices.

## Retained server management coverage (CHG-002)

The optional server desktop is retained infrastructure specified in specs/SERVER.md. It is not a generated target or a client protocol extension; CHG-002 left targets.json and the generic runner/prompt unchanged. The full verification command now includes server-gui lifecycle/monitoring checks and desktop/browser interoperability against a GUI-managed server. Clean regeneration recreates both clients in the retained-only workspace and reruns those same assertions. Published client sources need no targeted replacement for this server-only change.

## CHG-003 registered shared extension

DIRECTORY.md is explicitly registered for both targets. It adds user announcements, directory observations and durable-receipt reports, plus GUI selectors. Both clients require actual harness regeneration; no manual behavioral patches. Generic orchestration and prompt templates remain unchanged. Expanded retained tests are frozen before each generation run and included in clean regeneration.


## CHG-004 presence and web layout inputs

PRESENCE.md is registered after DIRECTORY.md for explicit mode notifications. Both current clients implement it; TYPESCRIPT.md defines the compact desktop-style web layout. Preserve these completed requirements on regeneration. Generic orchestration/prompt remain unchanged.
