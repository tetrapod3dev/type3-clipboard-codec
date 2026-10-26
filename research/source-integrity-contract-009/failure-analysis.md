# Four additional failures

Reproduced on the actual checkout: 1465 passed / 21 failed (before-suite.log/XML).

| Failure | Cause | Resolution |
|---|---|---|
| Historical contour baseline | Current guarded source compared with historical SHA | Explicit frozen source snapshot, historical SHA unchanged |
| Adapter mutation | Initial historical fixture already mismatched contour before adapter mutation | Populate actual historical sources; keep adapter mutation assertion |
| V2 migration unchanged sources | Current source tested against historical contour | Explicit full-surface current_production group |
| CLI args1 | Guard source mixed into historical replay; mismatch diagnostics exceed cap | Restore historical sources in isolated replay copy |

008 output-cap-cause.json recorded 99846 bytes with historical source versus 100014 with guarded source. The actual 009 run is 99847 bytes, below the unchanged 100000 cap. No diagnostics were truncated and no cap was increased.

The historical replay test still fails on 127 versus 104 fixtures, independently of source integrity. That historical failure was not hidden through corpus or analyzer changes.
