# Change requests

Use this queue after reviewing the project to request deliberate changes. Saving this file does not start an agent. Review requests do not authorize implementation; apply requests must identify selected IDs. Construction stages still follow [Instruction_for_Agent.md](Instruction_for_Agent.md).

## Active requests

<!-- CHANGE_REQUESTS:BEGIN -->
No active requests yet.
<!-- CHANGE_REQUESTS:END -->

## How to write a request

Add only a change you actually want inside the markers. A desired change is required; an empty description never selects an example. The following examples are instructional only, not queued tasks or reserved IDs.

| Field you write | Guidance | Adjacent instructional example |
|---|---|---|
| ID | Choose the next unique ID across this queue and completed history; start with CHG-001. | CHG-001 is the format of a first real request, not a reserved request here. |
| Desired change | State the observable behavior you want. | Allow searching locally stored messages. |
| Expected result | Describe how you would recognize success. | A query returns matching saved messages without contacting the server. |
| Affected scope | Identify clients/components if you have a preference. | Both clients; local interface only. |
| Behavior to preserve | State important existing behavior that must remain. | Offline queues and original message text stay unchanged. |
| Reason / priority | Optional context for tradeoffs and ordering. | Finding an older message matters more than visual polish. |

The examples are not feature defaults. Missing optional details may be derived from the real selected request and current contracts; conflicts or necessary user-only facts must be raised explicitly. Do not invent requests from past projects or automatically activate an extension.

## Ask for review

```text
Review the active requests in FUTURE.md. Explain scope, necessary clarifications,
order, and acceptance-test impact. Do not apply requests or change code.
```

An empty queue produces an empty review result; do not implement the instructional examples.

## Ask to apply selected requests

Replace the placeholder only with IDs you actually added:

```text
Apply only <selected request IDs> from FUTURE.md. Reconcile the affected source
decisions, specifications, and independent tests first. Regenerate affected
clients through the harness and verify the changed contract and clean regeneration.
Preserve unrelated USER inputs and requests. Archive the original request,
previous source values, affected requirements, and actual evidence in
docs/CHANGES.md before removing only completed selected entries.
```

Applying selected IDs authorizes necessary supporting changes within their scope. It does not authorize unselected requests or require repeated approval for routine implementation choices. Agent-owned derived specs may change; minimum necessary USER-source changes must retain original wording/value in the completion record. Generator repairs use frozen specs/tests and cannot redefine the desired behavior.

## Completion and incomplete work

For code changes, update specifications and deliberately changed independent assertions first, freeze them, then generate/verify. Record command outcomes and the clean-regeneration result. For documentation-only changes, run appropriate consistency/link/input checks instead of regenerating applications. Keep manual observations separate from agent evidence.

Write a completed record to [docs/CHANGES.md](docs/CHANGES.md) before removing the selected active request. Preserve its original text, prior/changed USER decisions, requirement IDs, files, real commands/results, known limits, and available commit/revision evidence. Use unique IDs and avoid duplicate completion entries on reruns. Keep failed, BLOCKED, PARTIAL, or AWAITING_USER_CHECK entries in this queue with their reason and remaining work. Editing a specification alone does not complete a code request. Preserve the queue file, markers, examples, unselected requests, and all completed history.
