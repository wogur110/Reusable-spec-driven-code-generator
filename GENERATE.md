# Generation harness contract

Status: Stage 1 plan. Every project command/configuration path in this document is PLANNED — not implemented or verified. The runtime application contract lives in specs/; this document defines reusable orchestration.

## Inputs and target configuration

Implement generator/run.py using Python standard-library orchestration. Options: --spec-root specs, --config generator/targets.json, --target all|python|typescript (default all), optional --model and --codex overrides. Paths resolve against the project root. Validate configuration before invoking an agent: version, nonempty targets, declared spec existence, safe relative paths, unique non-overlapping output directories directly under generated/, required-output paths, bounded timeouts/repair rounds, and nonempty argument-vector commands. Reject unknown target or missing registered input as BLOCKED with nonzero exit. Semantic contradictions are reconciled from the decision/spec inventory before execution; do not pretend path validation proves semantic consistency.

The following is the complete initial configuration shape to implement in Stage 2; it is a Markdown example, not an existing manifest. Tool/model resolution fills the null model only after a successful preflight and records the choice in decisions/configuration.

```json
{
  "version": 1,
  "shared_specs": ["PRODUCT.md", "PROTOCOL.md", "ACCEPTANCE.md"],
  "extensions": [],
  "context_files": ["Instruction_for_Agent.md", "README.md", "AGENTS.md", "DESIGN.md", "GENERATE.md", "TESTING.md", "docs/DECISIONS.md"],
  "agent": {"tool": "codex", "binary": "codex", "model": null, "timeout_seconds": 600, "template": "generator/prompts/client.md"},
  "repair_rounds": 3,
  "total_timeout_seconds": 5400,
  "dependency_policy": {"python": "standard library only, Python >=3.10", "node": ">=22", "typescript": "5.9.3", "playwright": "1.56.1", "browser_runtime": "no dependencies or CDN"},
  "targets": {
    "python": {
      "specs": ["PYTHON.md"],
      "output": "generated/python-client",
      "required_files": ["main.py"],
      "managed_lockfiles": [],
      "checks": [["{python}", "scripts/build.py", "--target", "python"], ["{python}", "scripts/verify.py", "--suite", "python-interface"]]
    },
    "typescript": {
      "specs": ["TYPESCRIPT.md"],
      "output": "generated/typescript-web",
      "required_files": ["index.html", "styles.css", "src/main.ts", "package.json", "package-lock.json", "tsconfig.json"],
      "managed_lockfiles": ["package-lock.json"],
      "checks": [["{python}", "scripts/build.py", "--target", "typescript"]]
    }
  },
  "setup_command": ["{python}", "scripts/setup.py", "--skip-browser-install"],
  "verify_command": ["{python}", "scripts/verify.py", "--suite", "all", "--report", "{report}"],
  "verify_timeout_seconds": 600
}
```

Use argument arrays without shell interpolation. {python} is the current interpreter; {report} is an owned report path. Freeze config after any authorized readiness reconciliation. Config/prompt hashes identify the exact invocation. Only the selected platform specification is passed with shared inputs. An extension is active only when explicitly listed; its documented delta supersedes the stated baseline clauses and no others. Contradictory/undeclared deltas must be resolved before a run. No feature-specific code in the generic runner or prompt.

## Coding-tool readiness

Observed on 2026-11-01: global Codex CLI 0.142.5; local `codex exec --help` advertises stdin prompts, --sandbox workspace-write, --ephemeral, --skip-git-repo-check, --json, --color, -C, and --model. Version/help exited 0 with a read-only PATH-alias warning. This is interface evidence only. No model call, authentication readiness, sandbox write, or generation has been tested for this repository.

In Stage 2, choose an actually accessible binary/model using the same account/environment as the harness. An installed CLI's configured model is merely a candidate. Perform one minimal noninteractive request in an isolated disposable workspace, require successful completion, and then record binary/version/requested model and any reported effective model. If the service omits its effective ID, record UNREPORTED. If a compatible local CLI installation is necessary, use this project's own development-tool directory and a real exact lock; never copy another project's implementation or credentials. Account or sandbox failures block actual generation, not independent retained implementation work. Do not start an interactive login inside a child run or assume a paid/account entitlement.

Planned adapter invocation, with a verified model substituted as an argument:

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

Stage 2 creates generator/prompts/client.md with configuration-driven substitutions. It must identify selected target/output, complete input inventory, active extensions, authored required outputs, dependency policy, target checks run by the parent, and actual repair diagnostics. State that only selected output is editable and that no old implementation is supplied or to be searched for. Require complete code, independent implementation, normal storage/transport for test interfaces, and truthful check/blocker reporting. Do not embed messaging algorithms, feature names, finished source, or hard-coded messages in generic prompts. Do not ask a candidate to install dependencies or author fake locks; trusted setup owns these steps.

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

PLANNED — not implemented or verified: `python3 scripts/regenerate_check.py`. Make a fresh retained-input copy with no generated source or indirect source copies, Git history, previous agent sessions, transcripts, builds, or client stores. Standard installed interpreters/dependency download caches may be reused only if they cannot contain client implementations; record this environment reuse. Assert target directories are absent before generation. Freeze retained manifests, run setup, actual generator --target all, setup/build, and standalone baseline verification. Compare inventories/hashes afterward and preserve the original project. Record all command outcomes; this outer proof is never called by baseline verification itself.

Evolution execution is deferred. If a selected FUTURE request or separate explicit experiment is authorized, first define its spec delta, affected targets, intended independent test changes, migration checks, and any retained server support. Freeze that revised contract; run the ordinary harness with registered extensions, baseline checks where applicable, and new checks. Verify generic runner/adapter/prompt hashes are unchanged to demonstrate adaptation from specs/configuration alone. Retain the reproducible delta/evidence. An isolated experiment must leave baseline source and the FUTURE queue unchanged. Do not pre-create a label or other feature specification in this Stage 1.
