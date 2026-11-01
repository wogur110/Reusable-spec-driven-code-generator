You are generating one explicitly selected target in an isolated workspace.
This task authorizes implementation only inside the selected output boundary.
It does not start a construction stage, invoke another generator, or authorize delegation.
Read the supplied workflow context and every registered specification below.
Current registered specifications define the required behavior.
Use only these inputs and this target's candidate during repair. Do not search
outside this workspace for source, Git history, other targets, or old transcripts.

Target: {target}
Writable source boundary: {output}
Registered specification inventory: {specs}
Workflow context: {context}
Active extensions: {extensions}
Required authored outputs: {required}
Dependency policy: {dependencies}
Trusted parent checks: {checks}

Implement complete, independent source satisfying the contracts. Test interfaces
must use production operations. Do not change any retained input, create files
outside the output boundary, edit Git history, or relax requirements.
Do not install dependencies, fabricate lockfiles, or run checks that write outside
the output boundary. The trusted parent installs dependencies, creates managed
locks, builds, and runs independent checks after you finish. Local syntax checks
that create no extra files are allowed. Report actual limitations truthfully.
Do not ask for approval of routine implementation choices already resolved by
the contracts. Finish the selected target within the available execution budget.

Actual repair diagnostics (empty for initial generation):
{diagnostics}
