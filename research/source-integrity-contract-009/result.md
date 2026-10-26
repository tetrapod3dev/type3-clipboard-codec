# Source Integrity Contract 009

Verdict: **SOURCE_INTEGRITY_CONTRACT_VERIFIED**.

Historical replay and Current Production source contracts are separated without editing production sources or the 008 Progress Guard. Historical SHA, raw provenance, original fixtures and frozen evidence are retained. A byte-exact historical Contour snapshot and explicit Current record/group were added.

Full Suite: **1465 PASS / 21 FAIL -> 1479 PASS / 17 historical FAIL**. All four additional failures are removed, no new failure IDs, no removed tests. Ten added checks account for the extra passing tests. Intentional source mutations and cross-contract version swaps are rejected.

Related checks: 204 PASS / 2 preexisting immutable research-lock FAIL. Their original locks remain unchanged. All 28 preserved V2 inputs reproduce complete semantic JSON. Normal Decoder fingerprints, 007 diagnostics and bounded-child Guard tests pass.

Historical CLI JSON is 99847 bytes under the unchanged 100000 cap. No cap, required diagnostic, or Decoder policy was changed.

Changed existing files: tests/source_integrity_baselines.json; tests/text_slot_v1_replay.py; the V2 migration test's explicit contract selection. Added: frozen Contour source copy and nine contract preservation/negative tests. See minimal-change.diff and preservation.json.

Remaining limitations: 17 historical Suite failures, two research execution-lock failures, unknown actual object boundaries and Group ownership. This verdict covers source integrity only. Selection 001-005 and original fixtures are preserved. No TypeEdit, Clipboard, Native, debugger or Git mutation operation was performed. Business mode remains OFF.

009 is complete. No object-framing research or runtime experiment was resumed.
