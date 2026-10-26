# Regression comparison

| Scope | Before | After |
|---|---:|---:|
| Full tests Suite | 1465 PASS / 21 FAIL | 1479 PASS / 17 FAIL |
| Historical failure IDs | 17 | Same 17 |
| Additional 008 failures | 4 | 0 |
| Added tests | - | 9 contract checks + 1 Current record parametrization |
| Removed tests | - | 0 |
| Related research/geometry checks | See existing records | 204 PASS / 2 preexisting research-lock FAIL |
| Preserved V2 samples | 28 JSON baselines | 28 complete semantic JSON matches |

Full suite command: `.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider tests -q --tb=short --junitxml=research/source-integrity-contract-009/after-suite.xml`, with PYTHONPATH=src and PYTHONDONTWRITEBYTECODE=1.

suite-comparison.json records exact resolved/retained/added/removed test IDs, and full before/after failure text for every retained failure. The retained test_all_runtime_outputs_and_source_bytes_unchanged now reaches its pre-008 runtime_outputs_equal failure instead of failing earlier at contour SHA. Other retained assertion differences remain visible in the JSON; identical IDs are not used to conceal cause/output changes.

Related checks include bounded-child Guard cases, eight complete normal Decoder fingerprints, 007 diagnostic equality, Inventory 001/002/V2, 006/007, geometry tests and archive-crosswalk 001/002. Exact IDs/results are in related.xml/log.

The two research-lock failures are archive-crosswalk-001::test_saved_G1_H_crosswalk and archive-crosswalk-002::test_G1_H_previous_results_unchanged. The same IDs and old contour dependency lock cause appear in 008 targeted-tests.txt. These are distinct from the full tests Suite's 17 historical failures. Original immutable locks were neither edited nor relaxed.

V2 equivalence removes only child_pid and elapsed_seconds telemetry; every other JSON field is compared. Baseline JSON is never overwritten. Run `python -B research/source-integrity-contract-009/verify_v2_equivalence.py`. Inventory 001/002 fresh results and 008 fingerprints are also covered by related pytest checks.
