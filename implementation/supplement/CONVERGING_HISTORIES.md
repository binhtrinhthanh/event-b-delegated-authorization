# Converging-history conformance experiment

Run from the repository root:

```sh
python3 implementation/supplement/check_converging_histories.py --output /tmp/converging_histories_results.json
```

The experiment uses the chain with allowance 1 and the star with allowance 2.
Breadth-first propagation retains at most eight distinct accepted command
prefixes per oracle state in deterministic command order. The cap also
applies to intermediate states, so the search samples histories within
this bound. Only states with at least two retained prefixes enter the
conformance trials.

Each prefix is executed on a fresh in-memory SQLite monitor through the
same adapter and dispatch paths used by the supplemental local scenarios.
The harness checks agreement during replay and then executes all 21
candidate commands after each prefix, with one outer savepoint per
candidate. It checks the decision, projected successor and the baseline
requirement checks. Counts include the trials for the first retained
prefix, some of which overlap the original single-prefix assessment.
The two experiment totals should be reported separately.

The checked-in JSON records the run totals. Timings depend on the host.
The experiment covers single-command continuations of the retained
accepted prefixes, under the existing assumptions and finite input
domains.
