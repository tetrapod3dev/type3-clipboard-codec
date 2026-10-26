# Historical and Current contracts

The source_integrity.py implementation, CRLF-to-LF-only canonical hashing, and return fields are unchanged. The caller explicitly selects a group; neither alternative-version acceptance nor hashes derived dynamically from checkout are used.

| Group | Meaning | Checked location |
|---|---|---|
| family | Original historical family SHA and legacy provenance | Isolated historical replay and historical mutation tests |
| current_production | Same 46 source paths, reviewed Text and Contour overrides only | Production checkout and V2 migration |
| current / style / approved_analyzers | Existing contracts | Unchanged |

Historical contour canonical SHA: `1882f894b333f6f3a005b4d0713d29bd0215ec5c9316e4b64f61d68ea61b65a4`.
Current contour canonical SHA: `a09b0e44f9a1e1066602e6fd451a5458e04c8c33c71570c0803cfe5b24061054`.
Current contour raw SHA: `94643e5c509ca469b453f2918ec4e31517bfa68157ac3646147f3e4bca492c87`.
Current provenance commit: `93d84a7453692206d423b3ab219324f1d466e242`; blob: `56eff30d41f05e96a4a8fe9bb7284a09dfd54b06`.

All preexisting record values and groups remain intact. Only frozen_snapshot_path metadata was added to the historical contour record. The new tests/frozen_contour_parser_pre_guard.py is byte-exactly the existing 008 contour_parser.before.py.txt. No preexisting frozen source or fixture was rewritten. Production does not import the frozen copy.

Historical CLI subprocesses execute frozen Text and Contour in a temporary source copy. The preexisting in-process replay_parser Text monkeypatch scope is unchanged; the current Contour's normal-output equivalence is checked independently by 008 fingerprints. Historical malformed-input execution was not added.

Negative tests mutate adapter and contour under each explicit contract and reject contour version swaps in both directions. Applying family to the actual current checkout still reports disagreement. Legacy raw differences remain provenance, never a substitute for canonical readiness.
