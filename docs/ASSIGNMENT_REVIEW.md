# Requirements and evidence review

Status: Stage 2 evidence review. The original source was available and compared; it is not included in the repository. [Source provenance](ASSIGNMENT.md) records its content hash and the intentional project additions. Actual baseline generation/interoperability and model access are demonstrated; clean proof and archive/history verification also pass. Evidence is linked from STATUS and EVIDENCE.json.

CHG-001 is complete. Desktop behavior, 55-case acceptance, and clean regeneration are demonstrated; the earlier failed proof remains disclosed in CHANGES/EVIDENCE. General user confirmation was received on 2026-11-01; detailed manual observations remain unrecorded.

CHG-002 is also complete: the optional retained server GUI passes the expanded 65-case suite, nine harness guards, and real all-client clean regeneration. Published clients and wire behavior remain unchanged. General user confirmation of CHG-002 was received on 2026-11-01; detailed manual observations and a current release archive remain pending.

CHG-003 is complete: 80 acceptance cases and nine harness guards pass. Clean proof 20261101T215733141945Z passes 80 cases inside the harness and standalone. Both clients were regenerated from the registered DIRECTORY extension; generic orchestration/prompt and version-1 stores remain unchanged. The initial 79/80 reset failure and bounded repair are disclosed in CHANGES/EVIDENCE. User review of CHG-003 and a current archive remain pending.

## Criterion mapping

| Review ID / criterion | Authoritative contract | Planned implementation and check | Current evidence |
|---|---|---|---|
| REV-01 / Design principles | DESIGN priorities; DECISIONS TD-01–TD-15 | Small server, clear client layers, explicit reliability limits; inspect actual design against these choices | Implemented; source layers and session limits match the contracts |
| REV-02 / Agent setup | AGENTS W01–W05; GENERATE readiness/isolation | Actual CLI/model preflight, selected-target prompts, bounded repair, integrity checks | Codex 0.166.0 + requested gpt-6-astra preflight and actual generation PASS |
| REV-03 / Generated boundaries | PRODUCT REQ-GEN-01; README folder map | Only generated/python-client and generated/typescript-web deleted/replaced; retained code stays | Implemented; nine AT-18 guards PASS, including rollback and allowlisting |
| REV-04 / Authorship | DESIGN ownership table; PRODUCT REQ-RELEASE-01 | Attribute retained agent work, child generation, package-manager output, and user observations truthfully | Parent retained work and actual harness-generated sources recorded in DESIGN/STATUS |
| REV-05 / Authentic history | Instruction guide; PRODUCT REQ-RELEASE-01 | Preserve actual incremental commits; inspect archive history, never synthesize a fake development sequence | Authentic commits include 7059ec8 retained implementation and f559d90 initial generated clients/regression, 2d57602 targeted regeneration, and c138989 verification gates; archive/history restoration PASS |
| REV-06 / Regeneration | PRODUCT REQ-GEN-02; GENERATE clean proof | AT-15 actual fresh generation, no prior clients/Git/source transcripts, same retained checks | AT-15 PASS: run 20261101T215733141945Z; 80 tests in harness and standalone verification |
| REV-07 / Authoritative specs | PRODUCT/PROTOCOL/PYTHON/TYPESCRIPT; DECISIONS | Resolve behavior from contract, not generated source; input fingerprints during repairs | Current 80-test suite PASS; frozen inputs and publication hashes in EVIDENCE.json |
| REV-08 / Interoperability | PRODUCT REQ-SEND-01 through REQ-RECEIVE-01; ACCEPTANCE | AT-02–AT-10, AT-13, AT-17 and both fixed-scenario role assignments | 80 acceptance tests PASS, including both client role assignments and GUI-managed server interoperability |
| REV-09 / Evolution | PRODUCT REQ-GEN-03; GENERATE extension inventory; FUTURE | Configured spec deltas, independent intended test changes, unchanged generic runner/prompt; real experiment only when requested | CHG-001–003 PASS: desktop/server interfaces and registered directory/receipt extension, unchanged generic runner/prompt, actual fresh regeneration and acceptance |
| REV-10 / Workspace structure | README roles; GENERATE input/output boundaries | Separate retained infrastructure from two independent outputs and disposable evidence | Retained infrastructure and two generated boundaries exist |
| REV-11 / Quality | ACCEPTANCE AT-01–AT-18; TESTING | Actual desktop/browser clients, external faults, deadlines, validation/persistence, immutable assertions and meaningful counts | 80 acceptance tests and nine guard tests PASS; optional fault injections disclosed |
| REV-12 / Future work | FUTURE markers; CHANGES completion contract | Review/apply selected real requests; archive evidence before removing completed items | CHG-001, CHG-002 and CHG-003 archived with original wording, preserved source decisions and actual evidence before completed active entries were removed |

## Cross-cutting constraints

| Constraint | Coverage / limitation |
|---|---|
| Local runtime and no messaging SDK | REQ-LOCAL-01, DESIGN dependency rationale, AT-14; actual local dependency/assets checks PASS |
| Fixed quoted exchange and original seven steps | ACCEPTANCE fixed scenario preserves them; eighth step verifies Bob's final queued delivery |
| Two independent languages | PYTHON and TYPESCRIPT contracts; separate target contexts and independent source implementations verified by actual interoperability checks |
| In-memory server | PROTOCOL session limit and TESTING reset steps agree; server implemented and protocol checks PASS |
| Review archive with real history | TESTING packaging/restoration contract; archive inventory and Git history restoration PASS |
| Human usability/restart evidence | User confirmed that the code works well; TESTING M01–M06 remain blank because individual scenario details were not supplied |

Documentary coverage is COMPLETE. Clients and retained infrastructure are implemented; expanded automated acceptance passes. Clean regeneration passes; Stage 2 and CHG-001–003 implementation are COMPLETE. The CHG-001 review archive passes source-inventory and Git-history restoration checks, as recorded in STATUS. Final release readiness remains NOT_READY: detailed manual observations and packaging of the current revision remain pending. These separate states must remain visible after implementation. CHG-001 demonstrates executed evolution; automated completion does not imply user sign-off. Optional OF-01/OF-02 storage/crash injection is deferred and cannot be claimed from a normal successful run.

Stage 2 updates each relevant row with actual revision/run IDs, command outcomes, counts, and spec/test hashes, plus any failing or missing prerequisite. For an authorized evolution change, state what contract changed and whether generic orchestration/prompt hashes remained equal. Do not mark a criterion demonstrated merely because its document or planned test exists.

CHG-002 mapping: REQ-SERVER-UI-01 and specs/SERVER.md map to SG-01–SG-06, covering actual widget/HTTP lifecycle and client interoperability. General user confirmation has been received for both CHG-001 and CHG-002; detailed individual scenario observations were not supplied. Existing archive results remain historical; packaging the current revision is separate.

CHG-003 mapping: specs/DIRECTORY.md and REQ-DIR-01/REQ-RECEIPT-01/REQ-ACTIVITY-01 map to DIR-01–08. The shared directory and cumulative acknowledgments preserve the required local messaging scenario, independent client queues and in-memory session limit. Presence is advisory and receipt claims are unauthenticated; offline client queues are unknown. No new runtime dependency or storage migration was added.
