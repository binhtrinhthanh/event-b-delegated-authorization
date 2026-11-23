# Formal Verification of Delegated Authorization in Agentic Systems

Reproducible pilot experiment, 25 October 2026.

Run `python3 experiment.py` with Python 3.12 or later. No dependencies. Outputs: results/results.json (including complete counterexamples and runtime environment) and results/summary.csv. The script asserts safety of all 12 correct configurations and detection of all 6 mutants.

Read MODEL.md for the state, transition rules, unchanged safety oracle, assumptions, and proposed Event-B development. Read REPORT_VI.md for interpretation and limitations.

## Interpretation of bounds
`n` counts the root user plus agents; jobs are fixed request identifiers. Tree topologies are chain and star. Scopes can take three nonempty values, but only read is exercised by jobs. Costs are one unit per job. Delegation is single issuance; revocation is irreversible. BFS has no search-depth cutoff, state cap, sampling, symmetry reduction, or timeout in the script. EXHAUSTED_SAFE means the entire reachable finite graph for that particular configuration was visited. It does not establish safety for arbitrary numbers of agents/jobs, nor correctness of the Python model itself.

The six faults are deliberately seeded model mutations, not independently collected real defects. Their detection is a sanity check of selected safeguards, not an unbiased estimate of real-world fault detection effectiveness. The same author produced model, requirements and checker. Neither Rodin nor ProB is used. No proof-obligation counts, automatic-proof percentages, external deployment results or LLM results are claimed.

## External motivation (not experimental evidence)
MCP authorization guidance documents audience binding and confused-deputy risks:
https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2025-11-25/basic/authorization.mdx
Rodin documentation identifies invariant preservation proof obligations:
https://wiki.event-b.org/index.php/Proof_Obligation_Names_%28Rodin_User_Manual%29

This pilot does not implement audience binding or evaluate conformance to MCP.
