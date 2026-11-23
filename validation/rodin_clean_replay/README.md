# Delegated Authorization — clean Rodin replay

This validation starts with a new Rodin workspace, importing only the six Event-B source files (.buc and .bum). The batch application runs Rodin's static checker and proof-obligation generator, then applies the artifact's DelegatedAuto profile through the native AutoProver.

The clean run generated 109 proof obligations and automatically discharged all 109, with zero static errors and no manually marked proofs. The inventory matches the archived inventory exactly by component, obligation name, confidence, status and manual-proof flag. The imported model sources are byte-identical to the archived artifact.

- `DelegatedAuthorization/` contains the Rodin project and the proofs generated in this run.
- `rodin_native.log` contains the build and proof status output.
- `po_inventory.csv` lists all 109 obligations.
- `native_summary.json` records version details, counts and source hashes.

Rodin 3.8.0.202304051545-af2f57e1e and Atelier B Provers core 1.7.1.r16756 with Linux bundle 2.4.0.r16756 match the archived environment. The new run used OpenJDK 21.0.13. The archive reports OpenJDK 17.0.20 for the original run.

To reproduce from the repository root, install Rodin and Atelier B Provers, then run:

```sh
python tools/run_rodin.py --rodin /path/to/rodin --work /path/to/new-empty-directory
```

Use `--ecj /path/to/ecj.jar` when `javac` is unavailable. The command above uses the unchanged batch runner included in the repository. The proof results in this evidence package concern the baseline model.
