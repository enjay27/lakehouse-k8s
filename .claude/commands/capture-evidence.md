---
description: Bank a run's outputs as evidence under diagnostics/outputs/banked/
---
Bank the outputs of the run named in $ARGUMENTS as durable evidence.

1. Locate the run's artifacts. Manifests and JSON belong in
   `diagnostics/outputs/banked/runs/`, rendered reports in
   `diagnostics/outputs/banked/reports/`, and index baselines in
   `diagnostics/outputs/banked/baselines/`.
2. Never bank anything from `diagnostics/outputs/captures/` -- that tree is
   gitignored by design and runs to hundreds of MB.
3. Record the run id, the Polaris version it drove, and the denominator it was
   measured against. `run_manifest.py`: *the manifest carries values, the live
   cluster carries truth, never one without the other.*
4. If the denominator moved since the run, say so explicitly -- a figure whose
   fingerprint is unrecorded is not reproducible, and `assert_denominator`
   hard-fails on drift.
5. Commit the banked files together with the finding that they support, in the
   same commit. Evidence committed separately from its conclusion goes stale.
