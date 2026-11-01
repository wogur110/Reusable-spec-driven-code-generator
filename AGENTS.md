# Project agent instructions

Read [Instruction_for_Agent.md](Instruction_for_Agent.md) first. Follow the user's active scope. Reading/reviewing does not authorize writes; guide revisions do not execute a stage. An explicit bootstrap request with no stage defaults to Stage 1. A Stage 2 request authorizes its ordinary supporting work and reconciliation; do not repeatedly ask about already authorized technical choices.

## Your working preferences

Blank preferences use adjacent defaults. Preserve all USER blocks and their meanings on revision.

<!-- USER:BEGIN WORKFLOW_CHOICES -->
| ID | Question | Your input | Example / automatic default |
|---|---|---|---|
| W01 | Which coding tool should the harness invoke? | | Codex; Claude Code is the other permitted choice. |
| W02 | How should a generation model be selected? | | Use a model actually available to the same authenticated CLI/account as the harness; verify one noninteractive request. Record the tool version, requested model, and effective model when reported; otherwise record the effective model as `UNREPORTED`. No hard-coded model is assumed to work. |
| W03 | How should routine technical decisions be handled? | | Choose a minimal compatible implementation, record the rationale, and continue; ask only when explicit requirements conflict or necessary user-only information is missing. |
| W04 | What are the repair and test limits? | | Up to 3 client repair attempts after initial generation; 30 seconds per observable messaging transition, with separate bounded build and tool timeouts. |
| W05 | How should progress be reported? | | Brief updates at meaningful milestones, with actual results, blockers, and next steps. |
<!-- USER:END WORKFLOW_CHOICES -->

## Authority and input preservation

The user supplies intent and observations; source USER tables hold preferences, [docs/DECISIONS.md](docs/DECISIONS.md) resolves them, and current registered specs define behavior. Preserve blank cells and source wording. Never turn adjacent defaults or observation examples into user-authored inputs or facts. Compare changed source values with the last reconciled snapshot; unchanged blanks do not erase later authorized requirements or extensions. If requirements genuinely conflict, document the conflict and continue independent authorized work.

Baseline active shared files: specs/PRODUCT.md, specs/PROTOCOL.md, specs/ACCEPTANCE.md. Python additionally reads specs/PYTHON.md; TypeScript reads specs/TYPESCRIPT.md. Extensions start empty and are registered explicitly. Do not recursively activate every Markdown file or treat FUTURE examples as features. External source files are read-only references; public provenance uses neutral source IDs/hashes and omits private paths/company framing.

## Stage and write boundaries

Stage 1 creates/reconciles the 16 required Markdown documents only. No application/harness code, executable tests, manifests, lockfiles, installed dependencies, generation requests, or runtime test claims. Read-only environment/document checks and explanatory fenced schemas/commands are permitted. Label planned interfaces PLANNED — not implemented or verified. Stop after documentation readiness and the user's edit map.

In full Stage 2, author retained server/tests/scripts/harness from the current contracts, then use the actual harness for client generation. A nested target-generation request authorizes only its supplied candidate output directory. It is not permission to bootstrap the project recursively, modify retained docs/specs/tests/server/harness/history, or read another client's implementation. No existing/sibling client source, Git objects, old transcripts, or hidden finished templates may substitute for generation.

Only generated/python-client/ and generated/typescript-web/ are published client regeneration boundaries. Stage candidates in isolated workspaces; verify input inventories/hashes after each agent call and trusted check. Reject source symlinks/path escapes and retained mutations. Keep published source until required checks pass, and rollback publication on failure. Never modify a sibling project. [GENERATE.md](GENERATE.md) defines the complete procedure.

## Verification discipline

Author retained tests independently from the written contracts before generating clients. Use actual CLI operations, browser controls, and external per-client transport faults while the server stays alive. Never delete/weaken assertions, hide failures with skips/retries, accept zero collected tests, or claim runtime success from compilation alone. Three repair rounds follow initial generation; concrete deadlines are in GENERATE.md. Agent repairs cannot change retained contracts or tests. An intentional feature change revises specs/tests first and begins a separately recorded run.

Implemented entry points (consult STATUS for actual results and pending checks):

```sh
python3 scripts/check_environment.py
python3 scripts/setup.py
python3 generator/run.py --target all
python3 scripts/setup.py
python3 scripts/verify.py --suite all
python3 scripts/verify.py --suite harness
python3 scripts/regenerate_check.py
```

Baseline verification excludes regeneration/evolution to prevent recursive generation. Model authentication, native browser prerequisites, and sandbox state access are environment facts; check them in Stage 2 without disabling host policy. Use installed tool help and official documentation for the actual flags. Record requested/effective model separately and use UNREPORTED when the service supplies no effective ID.

## Change requests and evidence

Read [FUTURE.md](FUTURE.md) only within the user's requested review/apply scope. Review alone applies nothing. Apply selected IDs by reconciling affected decisions/specs/tests, regenerating affected clients, and verifying the intended contract. Archive original wording, previous source values, actual results, and revision evidence in docs/CHANGES.md before removing only completed selected requests. Partial, blocked, failed, or user-check-pending items remain. Documentation-only changes use document checks.

Manual M01–M06 belong to the user; agent/automated observations go elsewhere. Record actual authorship, scope, failures, hashes, commands, and unverified limits in docs/STATUS.md and docs/ASSIGNMENT_REVIEW.md. Preserve authentic incremental Git history. Distinguish Stage 2 implementation completion, deferred evolution, user review, and archive/release readiness. No extra feature experiment is authorized by an empty FUTURE queue.
