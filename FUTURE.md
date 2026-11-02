# Change requests

Use this queue for future deliberate changes. CHG-001–004 are completed and archived in [docs/CHANGES.md](docs/CHANGES.md); current specifications already include them. Regeneration follows [the README default workflow](README.md#default-regeneration-instruction), including changed USER choices, and does not apply this queue. Saving this file starts no work; review authorizes no implementation and apply requests must select IDs.

## Active requests

<!-- CHANGE_REQUESTS:BEGIN -->

CHG-005: Add an automated network-failure test panel
- State: PROPOSED
- Change: Provide a separate local test panel that can interrupt either client's actual API traffic, execute reproducible failure scenarios, and report messaging outcomes.
- Scope: Retained test infrastructure, a small local control panel, headless scenario execution, transport-fault fixtures, evidence, and testing documentation.
- Dependencies: Working baseline clients, server, and integration tests. The panel can operate with the Python CLI or GUI;
- Priority: High. Useful before additional messaging features.

CHG-006: Support small file attachments in both clients
- State: PROPOSED
- Change: Let users attach a small file to an addressed message in the Python and TypeScript GUIs, queue it locally while offline, and retrieve/save the original bytes after delivery.
- Scope: Product and protocol extensions, both client interfaces and stores, server attachment storage, per-user message views, retained tests, generation inputs, and operating documentation.
- Dependencies: CHG-001 and CHG-003 completed and verified, including the server GUI.  Persistent server storage is not part of this request.
- Priority: Normal. Apply after existing text messaging and receipt behavior are stable.

CHG-007: Extend the generator with a Kotlin Android client target
- State: PROPOSED
- Change: Add a native Kotlin Android client as a third generated target, using the existing shared messaging specification and local server.
- Reason: Demonstrate that the generator can extend to another language and platform through written contracts and target configuration, while retaining reproducible generation and interoperability.
- Scope: A Kotlin platform specification, target/capability declarations, retained harness and Android test support, generated Android project, local emulator setup, operating documentation, and verification evidence.
- Dependencies: A working generation harness, shared protocol, local server, and verified Python/TypeScript baseline. The numbered GUI, presence, and attachment proposals are not automatic prerequisites; features already mandatory in the current accepted shared contract must be handled as specified below.
- Priority: Normal. Apply after baseline interoperability and regeneration are proven.
<!-- CHANGE_REQUESTS:END -->

## How to write a request

Add only a change you actually want inside the markers. A desired change is required; an empty description never selects an example. The following examples are instructional only, not queued tasks or reserved IDs.

| Field you write | Guidance | Adjacent instructional example |
|---|---|---|
| ID | Choose the next unique ID across this queue and completed history; CHG-001–004 are already used. | CHG-NNN is the format; assign an unused number only when adding a real request. |
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
decisions, specification sheets, independent tests, and preference-table
default/example columns before freezing inputs. Regenerate affected clients
through the harness and verify the changed contract and clean regeneration.
Update code and operating docs; check that specs/docs/defaults match the finished
result. Preserve my input/observation cells and unrelated requests. Record
previous/new defaults and their rationale. Archive original wording, changed
source values/defaults, affected requirements and actual evidence in
docs/CHANGES.md before removing only completed selected entries.
Keep failed or incomplete work clearly labeled rather than calling it finished.
```

Applying selected IDs authorizes necessary supporting changes within their scope. It does not authorize unselected requests or require repeated approval for routine implementation choices. Agent-owned derived specs may change; minimum necessary USER-source changes must retain original wording/value in the completion record. Generator repairs use frozen specs/tests and cannot redefine the desired behavior.

## Completion and incomplete work

For code changes, update specifications and deliberately changed independent assertions first, freeze them, then generate/verify. Record command outcomes and the clean-regeneration result. For documentation-only changes, run appropriate consistency/link/input checks instead of regenerating applications. Keep manual observations separate from agent evidence.

Completion also requires affected default/example columns to match the resulting code, specifications and operating instructions. Apply the [agent completion rule](AGENTS.md#future-development-completion-rule): record previous/new defaults, preserve actual USER inputs, and report unchanged defaults when no update is needed. Unselected requests remain outside current specifications/defaults.

Write a completed record to [docs/CHANGES.md](docs/CHANGES.md) before removing the selected active request. Preserve its original text, prior/changed USER decisions, requirement IDs, files, real commands/results, known limits, and available commit/revision evidence. Use unique IDs and avoid duplicate completion entries on reruns. Keep failed, BLOCKED, PARTIAL, or AWAITING_USER_CHECK entries in this queue with their reason and remaining work. Editing a specification alone does not complete a code request. Preserve the queue file, markers, examples, unselected requests, and all completed history.
