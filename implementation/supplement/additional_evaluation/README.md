# Additional Evaluation Evidence

This directory contains the supplementary experiments for *Formal
Verification of Delegated Authorization in Agentic Workflows with Staged
Execution*. The experiments build on [baseline commit `4f6695a`](https://github.com/binhtrinhthanh/event-b-delegated-authorization/tree/4f6695a5efc40b7e168abff1223e61fcbf2c058a).

## Deeper branching configuration

In a disposable checkout of the baseline, copy the supplied
[`implementation/supplement/check_deep_branches.py`](implementation/supplement/check_deep_branches.py)
to the same path relative to the repository root. From the root, run:

```bash
python3 implementation/supplement/check_deep_branches.py
```

The script writes `deep_branches_results.json`. The configuration
uses the two existing tool capabilities. The recorded results cover
12 selected traces and 156 command trials.

## Rodin timings

The supplied
[`BuildDelegation.java`](tools/headless/src/delegated/BuildDelegation.java)
measures elapsed time around each AutoProver call using
`System.nanoTime()`. Copy it to `tools/headless/src/delegated/` in a
disposable checkout, then follow the clean headless replay instructions
in the repository README.

[`rodin_timed/`](rodin_timed/) contains the native log and collector
summary. The total AutoProver time is the sum of the `AUTOPROVER_NS`
values in the log.

## Additional ProB reachability searches

Each variant directory under [`additional_goals/`](additional_goals/)
contains the exported Event-B model, the ProB log, and the concrete
reachability trace. Set `GOAL` to the exact predicate recorded for the
variant in [`additional_goals/summary.json`](additional_goals/summary.json).
Then run ProB CLI 1.16.1 from that variant's directory:

```bash
probcli model.eventb -model_check -nodead -p MAX_OPERATIONS 1000 \
  -p NUMBER_OF_ANIMATED_ABSTRACTIONS 0 -p PROOF_INFO false \
  -goal "$GOAL" -bf -his rerun_trace.json -his_option json \
  -his_option show_states
```

The searches reached the specified violation predicates in all four
variants. The two previously reported reachability witnesses are
available in the baseline artifact.
