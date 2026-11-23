# Cross-branch revocation figure

[cross_branch_revocation.pdf](cross_branch_revocation.pdf) visualizes the
`cross_branch` trace in
[local_results.json](../../implementation/supplement/local_results.json).
The three panels show the full allowance before revocation, both rejected
commands after revocation, and the successful retry after cancellation.

To regenerate the vector PDF, run the following from the repository root
with Python and Matplotlib installed.

```sh
python docs/figures/plot_cross_branch.py
```
