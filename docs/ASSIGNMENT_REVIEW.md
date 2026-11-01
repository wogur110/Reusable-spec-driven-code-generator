# Requirements and evidence review

Status: Stage 1 documentary coverage. The original source was available and compared; it is not included in the repository. [Source provenance](ASSIGNMENT.md) records its content hash and the intentional project additions. No code, interoperability, regeneration, or model-access success is claimed here.

## Criterion mapping

| Review ID / criterion | Authoritative contract | Planned implementation and check | Current evidence |
|---|---|---|---|
| REV-01 / Design principles | DESIGN priorities; DECISIONS TD-01–TD-15 | Small server, clear client layers, explicit reliability limits; inspect actual design against these choices | Documented; implementation NOT_STARTED |
| REV-02 / Agent setup | AGENTS W01–W05; GENERATE readiness/isolation | Actual CLI/model preflight, selected-target prompts, bounded repair, integrity checks | Interface/version observations only; authenticated access UNVERIFIED |
| REV-03 / Generated boundaries | PRODUCT REQ-GEN-01; README folder map | Only generated/python-client and generated/typescript-web deleted/replaced; retained code stays | Documented; AT-18 NOT_RUN |
| REV-04 / Authorship | DESIGN ownership table; PRODUCT REQ-RELEASE-01 | Attribute retained agent work, child generation, package-manager output, and user observations truthfully | Stage 1 authorship recorded; generated code NOT_STARTED |
| REV-05 / Authentic history | Instruction guide; PRODUCT REQ-RELEASE-01 | Preserve actual incremental commits; inspect archive history, never synthesize a fake development sequence | Guide commit 216ef72 exists; Stage 2 history/archive NOT_CREATED |
| REV-06 / Regeneration | PRODUCT REQ-GEN-02; GENERATE clean proof | AT-15 actual fresh generation, no prior clients/Git/source transcripts, same retained checks | Planned; NOT_RUN |
| REV-07 / Authoritative specs | PRODUCT/PROTOCOL/PYTHON/TYPESCRIPT; DECISIONS | Resolve behavior from contract, not generated source; input fingerprints during repairs | Contracts cross-checked; runtime adherence NOT_RUN |
| REV-08 / Interoperability | PRODUCT REQ-SEND-01 through REQ-RECEIVE-01; ACCEPTANCE | AT-02–AT-10, AT-13, AT-17 and both fixed-scenario role assignments | Planned; NOT_RUN |
| REV-09 / Evolution | PRODUCT REQ-GEN-03; GENERATE extension inventory; FUTURE | Configured spec deltas, independent intended test changes, unchanged generic runner/prompt; real experiment only when requested | Generic design documented; executed evolution NOT_RUN / deferred |
| REV-10 / Workspace structure | README roles; GENERATE input/output boundaries | Separate retained infrastructure from two independent outputs and disposable evidence | Markdown structure exists; implementation structure NOT_STARTED |
| REV-11 / Quality | ACCEPTANCE AT-01–AT-18; TESTING | Actual clients/browser, external faults, deadlines, validation/persistence, immutable assertions and meaningful counts | Documentation checks complete; executable tests NOT_RUN |
| REV-12 / Future work | FUTURE markers; CHANGES completion contract | Review/apply selected real requests; archive evidence before removing completed items | Queue and completion history correctly empty |

## Cross-cutting constraints

| Constraint | Coverage / limitation |
|---|---|
| Local runtime and no messaging SDK | REQ-LOCAL-01, DESIGN dependency rationale, AT-14; actual dependencies/assets NOT_RUN |
| Fixed quoted exchange and original seven steps | ACCEPTANCE fixed scenario preserves them; eighth step verifies Bob's final queued delivery |
| Two independent languages | PYTHON and TYPESCRIPT contracts; source and runtime independence remain to be demonstrated |
| In-memory server | PROTOCOL session limit and TESTING reset steps agree; server implementation NOT_STARTED |
| Review archive with real history | TESTING packaging/restoration contract; archive NOT_CREATED |
| Human usability/restart evidence | TESTING M01–M06 blank; manual review PENDING; automated tests cannot fill these facts |

Documentary coverage is COMPLETE for Stage 1. Implementation is NOT_STARTED; automated acceptance and clean regeneration are NOT_RUN; final release readiness is NOT_READY. These separate states must remain visible after implementation. Baseline completion does not imply executed evolution or user sign-off. Optional OF-01/OF-02 storage/crash injection is deferred and cannot be claimed from a normal successful run.

Stage 2 updates each relevant row with actual revision/run IDs, command outcomes, counts, and spec/test hashes, plus any failing or missing prerequisite. For an authorized evolution change, state what contract changed and whether generic orchestration/prompt hashes remained equal. Do not mark a criterion demonstrated merely because its document or planned test exists.
