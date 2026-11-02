# Requirements and evidence review

Status: requirements review through completed CHG-004. The original source was compared and remains excluded from the repository; [source provenance](ASSIGNMENT.md) records that historical comparison. The last implementation snapshot passed 92 acceptance tests, nine guards and clean regeneration. Earlier archive/history verification passed for its recorded revision; current packaging and detailed manual review remain pending. Documentation reconciliation updates current defaults/contracts without creating new runtime evidence. Historical outcomes follow.

CHG-001 is complete. Desktop behavior, 55-case acceptance, and clean regeneration are demonstrated; the earlier failed proof remains disclosed in CHANGES/EVIDENCE. General user confirmation was received on 2026-11-01; detailed manual observations remain unrecorded.

CHG-002 is also complete: the optional retained server GUI passes the expanded 65-case suite, nine harness guards, and real all-client clean regeneration. Published clients and wire behavior remain unchanged. General user confirmation of CHG-002 was received on 2026-11-01; detailed manual observations and a current release archive remain pending.

CHG-003 is complete: 80 acceptance cases and nine harness guards pass. Clean proof 20261101T215733141945Z passes 80 cases inside the harness and standalone. Both clients were regenerated from the registered DIRECTORY extension; generic orchestration/prompt and version-1 stores remain unchanged. The initial 79/80 reset failure and bounded repair are disclosed in CHANGES/EVIDENCE. User review of CHG-003 and a current archive remain pending.

## CHG-004 complete

Both clients explicitly notify the server when their Development transport changes, and the web interface follows the Python desktop layout. Server Offline state is independent of peer message traffic and cannot be undone by a late legacy heartbeat. Real connection loss still uses heartbeat expiry. Published generation 20261101T230328364307Z passed 92/92; calls per target: {'python': 1, 'typescript': 1}. Nine harness guards pass. Clean proof 20261101T232007378344Z passed 92/92 inside the harness and 92/92 standalone and preserved the original tree; fresh calls per target: {'python': 3, 'typescript': 3}.

The first run was intentionally stopped after a compiler repair and a 90/92 result: Python reset exposed stale rows, and an isolated probe proved Chromium automatically retried the lost-reply fixture. The corrected fixture withholds the accepted reply until the client deadline. All acceptance assertions remained unchanged; a new generation run used fresh candidates. Exact hashes and reports are recorded in EVIDENCE.json. USER blocks and generic generator/prompt remain unchanged. User manual review and a current release archive remain pending.

## Criterion mapping

| Review ID / criterion | Authoritative contract | Planned implementation and check | Current evidence |
|---|---|---|---|
| REV-01 / Design principles | DESIGN priorities; DECISIONS TD-01–TD-15 | Small server, clear client layers, explicit reliability limits; inspect actual design against these choices | Implemented; source layers and session limits match the contracts |
| REV-02 / Agent setup | AGENTS W01–W05; GENERATE readiness/isolation | Actual CLI/model preflight, selected-target prompts, bounded repair, integrity checks | Codex 0.166.0 + requested gpt-6-astra preflight and actual generation PASS |
| REV-03 / Generated boundaries | PRODUCT REQ-GEN-01; README folder map | Only generated/python-client and generated/typescript-web deleted/replaced; retained code stays | Implemented; nine AT-18 guards PASS, including rollback and allowlisting |
| REV-04 / Authorship | DESIGN ownership table; PRODUCT REQ-RELEASE-01 | Attribute retained agent work, child generation, package-manager output, and user observations truthfully | Parent retained work and actual harness-generated sources recorded in DESIGN/STATUS |
| REV-05 / Authentic history | Instruction guide; PRODUCT REQ-RELEASE-01 | Preserve actual incremental commits; inspect archive history, never synthesize a fake development sequence | Authentic commits include 7059ec8 retained implementation and f559d90 initial generated clients/regression, 2d57602 targeted regeneration, and c138989 verification gates; archive/history restoration PASS |
| REV-06 / Regeneration | PRODUCT REQ-GEN-02; GENERATE clean proof | AT-15 actual fresh generation, no prior clients/Git/source transcripts, same retained checks | AT-15 PASS: run 20261101T232007378344Z; 92 tests in harness and standalone verification |
| REV-07 / Authoritative specs | PRODUCT/PROTOCOL/PYTHON/TYPESCRIPT; DECISIONS | Resolve behavior from contract, not generated source; input fingerprints during repairs | Current 92-test suite PASS; frozen inputs and publication hashes in EVIDENCE.json |
| REV-08 / Interoperability | PRODUCT REQ-SEND-01 through REQ-RECEIVE-01; ACCEPTANCE | AT-02–AT-10, AT-13, AT-17 and both fixed-scenario role assignments | 92 acceptance tests PASS, including both client role assignments and GUI-managed server interoperability |
| REV-09 / Evolution | PRODUCT REQ-GEN-03; GENERATE registered inventory | Deliberate spec/test changes, unchanged generic runner/prompt, actual generation and clean proof | CHG-001–004 PASS: client/server interfaces, DIRECTORY/PRESENCE, durable receipts, explicit mode updates and compact browser layout |
| REV-10 / Workspace structure | README roles; GENERATE input/output boundaries | Separate retained infrastructure from two independent outputs and disposable evidence | Retained infrastructure and two generated boundaries exist |
| REV-11 / Quality | ACCEPTANCE AT-01–AT-18; TESTING | Actual desktop/browser clients, external faults, deadlines, validation/persistence, immutable assertions and meaningful counts | 92 acceptance tests and nine guard tests PASS; optional fault injections disclosed |
| REV-12 / Future work | FUTURE markers; CHANGES completion contract | Review/apply selected real requests; archive evidence before removing completed items | CHG-001–004 archived with original wording, preserved source decisions and actual evidence before completed active entries were removed |

## Cross-cutting constraints

| Constraint | Coverage / limitation |
|---|---|
| Local runtime and no messaging SDK | REQ-LOCAL-01, DESIGN dependency rationale, AT-14; actual local dependency/assets checks PASS |
| Fixed quoted exchange and original seven steps | ACCEPTANCE fixed scenario preserves them; eighth step verifies Bob's final queued delivery |
| Two independent languages | PYTHON and TYPESCRIPT contracts; separate target contexts and independent source implementations verified by actual interoperability checks |
| In-memory server | PROTOCOL session limit and TESTING reset steps agree; server implemented and protocol checks PASS |
| Review archive with real history | Earlier revision passed TESTING packaging/restoration checks; current revision still requires its own archive |
| Human usability/restart evidence | User confirmed that the code works well; TESTING M01–M06 remain blank because individual scenario details were not supplied |

Documentary coverage includes all completed CHG-001–004 requirements and the default choice-reconciliation workflow. Clients and retained infrastructure are implemented; recorded acceptance, guards and clean regeneration passed at the hashes in EVIDENCE.json. This documentation-only update has no new runtime test result. The prior CHG-001 archive passed restoration; final release readiness remains NOT_READY until detailed manual observations and current packaging are complete. Optional OF-01/OF-02 crash/storage injection remains deferred.

Stage 2 updates each relevant row with actual revision/run IDs, command outcomes, counts, and spec/test hashes, plus any failing or missing prerequisite. For an authorized evolution change, state what contract changed and whether generic orchestration/prompt hashes remained equal. Do not mark a criterion demonstrated merely because its document or planned test exists.

CHG-002 mapping: REQ-SERVER-UI-01 and specs/SERVER.md map to SG-01–SG-06, covering actual widget/HTTP lifecycle and client interoperability. General user confirmation has been received for both CHG-001 and CHG-002; detailed individual scenario observations were not supplied. Existing archive results remain historical; packaging the current revision is separate.

CHG-003 mapping: specs/DIRECTORY.md and REQ-DIR-01/REQ-RECEIPT-01/REQ-ACTIVITY-01 map to DIR-01–08. The shared directory and cumulative acknowledgments preserve the required local messaging scenario, independent client queues and in-memory session limit. Presence is advisory and receipt claims are unauthenticated; offline client queues are unknown. No new runtime dependency or storage migration was added.

CHG-004 maps REQ-PRESENCE-01 and REQ-WEB-UI-02 to PRES-01–05 and WEB-01. Explicit control traffic is a narrow exception to intentional offline mode; ordinary messages stay queued. The same independent clients, local server, fixed scenario, version-1 stores, and generic generation workflow are preserved.
