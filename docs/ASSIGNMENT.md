# Source requirements

**Project requirements summary verified against the supplied source.** This is a neutral summary, not a verbatim reproduction of the original reference.

| Provenance fact | Recorded value |
|---|---|
| Neutral source identifier | SRC-ORIGINAL-01, externally supplied requirements document |
| Source availability | AVAILABLE; read from the user-supplied external reference |
| Source SHA-256 | `fad9965065f7e792d99036aa5fa19c28f84704e9d65fb651ac298ad7033e825b` |
| Comparison | COMPARED on 2026-11-01, America/Los_Angeles |
| Original inclusion | NOT_INCLUDED; kept unmodified outside this repository |
| Construction guide | Instruction_for_Agent.md, baseline commit 216ef72 |
| Guide SHA-256 | `190a384ffce70396fa93fb02c6722b73f6a74bae5185e1ba9b0f540da5eda5fc` |
| Conflicts found | None between the compared core requirements and the selected baseline |

Private source paths and commissioning details are intentionally absent. NOT_INCLUDED means the original is not packaged here; it does not mean the source was unavailable or the comparison was not performed. Future source changes must trigger a new comparison and provenance entry before updating obligations.

## Verified obligations

| ID | Source obligation | Project realization / evidence |
|---|---|---|
| SRC-01 | Deliver a reusable generator driven by a written specification through Codex or Claude Code. | Codex selected by W01; declared harness contract in GENERATE.md, actual generation evidence in STATUS. |
| SRC-02 | Deleting the marked generated client source and invoking the generator recreates working clients. | Two explicit generated boundaries; fresh workspace proof AT-15 with unchanged acceptance tests. |
| SRC-03 | Implement two clients in different languages without shared messaging source. | Python and TypeScript selected; common written protocol, independently generated implementations. |
| SRC-04 | Identify a user by name, send addressed text, queue locally during outage, flush on reconnect, and display incoming messages. | PRODUCT requirements and PROTOCOL state/retry/durability contract. |
| SRC-05 | Support the specified Alice/Bob exchange and independent offline sequence. | Exact first two texts and original seven steps retained in ACCEPTANCE; explicit final Alice reconnect adds verification. |
| SRC-06 | Application runs locally without external runtime services or turnkey messaging SDKs; general-purpose libraries are allowed. | Local stdlib Python server, local browser assets, SQLite/IndexedDB clients. Generation-time tool authentication is separate. |
| SRC-07 | Keep the server small; in-memory operation is sufficient. | One process and locked memory streams/receipts; explicit client reset for new server sessions. |
| SRC-08 | Provide repository archive(s) with generated source and meaningful authentic commit history. | Single repository, source/lock inclusion, defined archive restoration proof; archive verification recorded in STATUS. |
| SRC-09 | Make harness, specs, generator usage, generated boundaries, server, and actual authorship easy to find. | README navigation, DESIGN ownership, AGENTS and GENERATE workflows. |
| SRC-10 | Demonstrate design judgment, quality, interoperability, authoritative specs, and suitability for evolving specifications. | Independent test plan and criterion mapping; distinguish baseline proof from deferred executed evolution. |

The source permits flexible harness/repository structure and language selection, and makes a future-work document optional. This project chooses one repository, Python/TypeScript, a Python orchestration CLI, and an initially empty FUTURE request workflow. Those are project choices, not claims that the source prescribed them.

## Explicit additions and limits

The eighth scenario step, restart-persistence checks, receipt-loss deduplication, strict validation, local schema contracts, three repair rounds, and 30-second observations make the selected behavior testable. The source's minimal behavior is preserved; these concrete project contracts are recorded as defaults/derived decisions in [DECISIONS.md](DECISIONS.md).

No additional feature or evolution experiment is active. The generic harness is designed to accept registered changes, but executed adaptation remains NOT_RUN until authorized. Required human sign-off is a project workflow step, distinct from automated acceptance and Stage 2 implementation completion. None of this source comparison establishes runtime compliance; see [ASSIGNMENT_REVIEW.md](ASSIGNMENT_REVIEW.md).
