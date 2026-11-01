# Requirements and evidence review

Status: Stage 2 evidence review. The original source was available and compared; it is not included in the repository. [Source provenance](ASSIGNMENT.md) records its content hash and the intentional project additions. Actual baseline generation/interoperability and model access are demonstrated; clean proof and archive/history verification also pass. Evidence is linked from STATUS and EVIDENCE.json.

## Criterion mapping

| Review ID / criterion | Authoritative contract | Planned implementation and check | Current evidence |
|---|---|---|---|
| REV-01 / Design principles | DESIGN priorities; DECISIONS TD-01–TD-15 | Small server, clear client layers, explicit reliability limits; inspect actual design against these choices | Implemented; source layers and session limits match the contracts |
| REV-02 / Agent setup | AGENTS W01–W05; GENERATE readiness/isolation | Actual CLI/model preflight, selected-target prompts, bounded repair, integrity checks | Codex 0.166.0 + requested gpt-6-astra preflight and actual generation PASS |
| REV-03 / Generated boundaries | PRODUCT REQ-GEN-01; README folder map | Only generated/python-client and generated/typescript-web deleted/replaced; retained code stays | Implemented; nine AT-18 guards PASS, including rollback and allowlisting |
| REV-04 / Authorship | DESIGN ownership table; PRODUCT REQ-RELEASE-01 | Attribute retained agent work, child generation, package-manager output, and user observations truthfully | Parent retained work and actual harness-generated sources recorded in DESIGN/STATUS |
| REV-05 / Authentic history | Instruction guide; PRODUCT REQ-RELEASE-01 | Preserve actual incremental commits; inspect archive history, never synthesize a fake development sequence | Authentic commits include 7059ec8 retained implementation and f559d90 initial generated clients/regression, 2d57602 targeted regeneration, and c138989 verification gates; archive/history restoration PASS |
| REV-06 / Regeneration | PRODUCT REQ-GEN-02; GENERATE clean proof | AT-15 actual fresh generation, no prior clients/Git/source transcripts, same retained checks | AT-15 PASS: run 20261101T133420994052Z; 44 tests in harness and standalone verification |
| REV-07 / Authoritative specs | PRODUCT/PROTOCOL/PYTHON/TYPESCRIPT; DECISIONS | Resolve behavior from contract, not generated source; input fingerprints during repairs | Expanded 44-test baseline PASS; frozen inputs and publication hashes in EVIDENCE.json |
| REV-08 / Interoperability | PRODUCT REQ-SEND-01 through REQ-RECEIVE-01; ACCEPTANCE | AT-02–AT-10, AT-13, AT-17 and both fixed-scenario role assignments | 44 baseline tests PASS, including both role assignments |
| REV-09 / Evolution | PRODUCT REQ-GEN-03; GENERATE extension inventory; FUTURE | Configured spec deltas, independent intended test changes, unchanged generic runner/prompt; real experiment only when requested | Generic design documented; executed evolution NOT_RUN / deferred |
| REV-10 / Workspace structure | README roles; GENERATE input/output boundaries | Separate retained infrastructure from two independent outputs and disposable evidence | Retained infrastructure and two generated boundaries exist |
| REV-11 / Quality | ACCEPTANCE AT-01–AT-18; TESTING | Actual clients/browser, external faults, deadlines, validation/persistence, immutable assertions and meaningful counts | 44 baseline tests and nine guard tests PASS; optional fault injections disclosed |
| REV-12 / Future work | FUTURE markers; CHANGES completion contract | Review/apply selected real requests; archive evidence before removing completed items | Queue and completion history correctly empty |

## Cross-cutting constraints

| Constraint | Coverage / limitation |
|---|---|
| Local runtime and no messaging SDK | REQ-LOCAL-01, DESIGN dependency rationale, AT-14; actual local dependency/assets checks PASS |
| Fixed quoted exchange and original seven steps | ACCEPTANCE fixed scenario preserves them; eighth step verifies Bob's final queued delivery |
| Two independent languages | PYTHON and TYPESCRIPT contracts; separate target contexts and independent source implementations verified by actual interoperability checks |
| In-memory server | PROTOCOL session limit and TESTING reset steps agree; server implemented and protocol checks PASS |
| Review archive with real history | TESTING packaging/restoration contract; archive inventory and Git history restoration PASS |
| Human usability/restart evidence | TESTING M01–M06 blank; manual review PENDING; automated tests cannot fill these facts |

Documentary coverage is COMPLETE. Clients and retained infrastructure are implemented; expanded automated acceptance passes. Clean regeneration and archive verification pass; Stage 2 implementation is COMPLETE. Final release readiness remains NOT_READY with required user manual review pending. These separate states must remain visible after implementation. Baseline completion does not imply executed evolution or user sign-off. Optional OF-01/OF-02 storage/crash injection is deferred and cannot be claimed from a normal successful run.

Stage 2 updates each relevant row with actual revision/run IDs, command outcomes, counts, and spec/test hashes, plus any failing or missing prerequisite. For an authorized evolution change, state what contract changed and whether generic orchestration/prompt hashes remained equal. Do not mark a criterion demonstrated merely because its document or planned test exists.
