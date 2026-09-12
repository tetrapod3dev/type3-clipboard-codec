# Frozen baseline integrity investigation

Date: 2026-09-13. Diagnosis only; no repair was performed.

## Main result

**baseline_status = multiple_causes**

1. Git checkout CRLF conversion breaks raw-byte checks for the frozen v1 source and current v2 slot source. Their LF, index and HEAD contents exactly match the applicable expected hashes.
2. The chain-parser and models-package expected hashes can be reproduced exactly using **unchanged HEAD text with mixed LF/CRLF endings**. Uniform LF or CRLF checkout cannot reproduce those historical byte snapshots.
3. The clipboard-adapter expected hash is not reproducible from working raw, LF, index, HEAD, uniform CRLF HEAD, or the reviewed historical blob variants. Its text has not changed since the baseline commit. The exact historical preimage remains unresolved; mixed endings or an uncommitted capture-time variant cannot be distinguished from available evidence. Do not assert actual adapter behavior changed.
4. The authorized archive-metadata commit changed two analyzer sources, while an older test still freezes their pre-promotion hashes. This is an additional **latent** hash failure masked by an earlier chain-parser assertion, not the cause of the ten currently reported failures.

No local uncommitted source edits were present at entry. No parser/adapter text restoration to HEAD is warranted. Blanket hash replacement is not justified.

## Git state and configuration

Repository: `C:\work\develop\type3-clipboard-codec`.
HEAD: `333d59bd32ee0aed8418edf806be9c9604e0e785`.
Branch: `master`.
Remote (fetch and push): `https://github.com/tetrapod3dev/type3-clipboard-codec.git`.

At investigation entry all of these returned empty output:
`git status --short`, `git diff --name-only`, `git diff --stat`, and the relevant-source `git diff`.
The archive metadata work is now committed in HEAD (2026-09-13 01:26:41 +0900);
it is not an uncommitted change. That commit changes only the two analyzers,
one new focused test, and the metadata document: 408 insertions across four files.
Its production `src` and fixture diff is empty.

- `core.autocrlf=true`, from `C:/Program Files/Git/etc/gitconfig`.
- `core.eol`, `core.safecrlf`, `core.attributesFile`: unset (query exit 1, no value).
- Repository-local config has no overrides for those keys.
- No repository/nested tracked `.gitattributes`, no applicable parent `.gitattributes`,
  and no `.git/info/attributes` were found.
- The default user attributes path `C:/Users/USER/.config/git/attributes` was absent.
- System `C:/Program Files/Git/etc/gitattributes` contains document/PDF diff-driver rules,
  with no applicable Python rule.
- `git check-attr -a -- <affected paths>` returned no attributes.
  Explicit `text`, `eol`, `working-tree-encoding`, and `filter` queries returned
  `unspecified` for the affected paths.
- For the frozen source, chain parser, clipboard adapter and models initializer,
  `git ls-files --eol` reports `i/lf w/crlf`.

No fetch/pull/reset/checkout, Git config change, attribute edit, source normalization
in place, expected-hash update, or readiness-test edit was performed.

## Hash method

SHA256 is computed over actual bytes using `hashlib.sha256`.
Git contents are obtained through binary `subprocess.check_output(["git","show",...])`;
the displayed values are **not Git object IDs** and are not shell-decoded text.

Four forms are recorded: working raw; working LF (`CRLF -> LF` in memory);
index blob (`:<path>`); HEAD blob (`HEAD:<path>`).
Raw and line-ending-independent comparisons are separate. No lone CR was removed.
All affected working/index/HEAD text comparisons after CRLF normalization are equal.
Only the analyzer files are also raw-byte equal to HEAD; the other listed files
differ from HEAD only in newline bytes. There are no working-vs-HEAD textual hunks.

Expected-hash forms differ across baseline files: some freeze CRLF, some LF,
and at least two freeze mixed endings. Normalizing every Python file to LF is
therefore not a complete solution.

## Four-form hash matrix

### tests/frozen_text_slot_candidate_v1.py

Expected: `76458eecec602b6e41f97c06b7188723fcf7a53e0bec1fe99445a586625d7d28`. Working endings: CRLF (131 CRLF, 0 bare LF).

| Form | SHA256 of actual contents |
| --- | --- |
| working_raw | `d5a1edf830633a20f3583ebb3a260033df14a70368dd57fdd710fb40ba80ed21` |
| working_LF | `76458eecec602b6e41f97c06b7188723fcf7a53e0bec1fe99445a586625d7d28` |
| index_contents | `76458eecec602b6e41f97c06b7188723fcf7a53e0bec1fe99445a586625d7d28` |
| HEAD_contents | `76458eecec602b6e41f97c06b7188723fcf7a53e0bec1fe99445a586625d7d28` |

Expected matches: working_LF, index_contents, HEAD_contents. Raw working=HEAD: False; LF working=LF HEAD: True.

### src/type3_clipboard_codec/parsers/text/text_slot_candidate.py

Expected: `31ff8567fe65c08ff9085d5433b1b533efc6978f540b6ed0d17dd735dba00876`. Working endings: CRLF (167 CRLF, 0 bare LF).

| Form | SHA256 of actual contents |
| --- | --- |
| working_raw | `877ed91f30be4b3748a77455ada1199c844e752de778c5a8f3cb0d5e56626c8c` |
| working_LF | `31ff8567fe65c08ff9085d5433b1b533efc6978f540b6ed0d17dd735dba00876` |
| index_contents | `31ff8567fe65c08ff9085d5433b1b533efc6978f540b6ed0d17dd735dba00876` |
| HEAD_contents | `31ff8567fe65c08ff9085d5433b1b533efc6978f540b6ed0d17dd735dba00876` |

Expected matches: working_LF, index_contents, HEAD_contents. Raw working=HEAD: False; LF working=LF HEAD: True.

### src/type3_clipboard_codec/parsers/type3_chain_parser.py

Expected: `9eed3128222722ca9300e3a3845600026c6562aec951c04772f86d22d03f9dbb`. Working endings: CRLF (815 CRLF, 0 bare LF).

| Form | SHA256 of actual contents |
| --- | --- |
| working_raw | `ec192403f28bb1da30a45867225f62f56f512fafe0e4253292d7ea992627b652` |
| working_LF | `8a7ffcc8eefa0315e6d299895dbaed9ca283cadb6618d04d5704664a7712931b` |
| index_contents | `8a7ffcc8eefa0315e6d299895dbaed9ca283cadb6618d04d5704664a7712931b` |
| HEAD_contents | `8a7ffcc8eefa0315e6d299895dbaed9ca283cadb6618d04d5704664a7712931b` |

Expected matches: none of the four forms. Raw working=HEAD: False; LF working=LF HEAD: True.

HEAD blob also equals the family-baseline creation commit blob.

Verified exact mixed-newline reconstruction matches expected SHA and normalizes back to HEAD.

### src/type3_clipboard_codec/adapters/win32_clipboard.py

Expected: `8b3b5ebf36498f5a8e7610528c2100b20ee506c2f6e468d89ed46005ebb3157c`. Working endings: CRLF (174 CRLF, 0 bare LF).

| Form | SHA256 of actual contents |
| --- | --- |
| working_raw | `f084c629cc6d8af5652b5f11c21f64ddd69f1102ebd2d87ba0f8a1fa9f4b668c` |
| working_LF | `9330510157a93c7059697e4bf988eae5c09870d71dec4b62353ee15fefe60014` |
| index_contents | `9330510157a93c7059697e4bf988eae5c09870d71dec4b62353ee15fefe60014` |
| HEAD_contents | `9330510157a93c7059697e4bf988eae5c09870d71dec4b62353ee15fefe60014` |

Expected matches: none of the four forms. Raw working=HEAD: False; LF working=LF HEAD: True.

HEAD blob also equals the family-baseline creation commit blob.

### src/type3_clipboard_codec/models/__init__.py

Expected: `74dfe83ee7f2b7b5b59249c782cb4092724f2fa4cdff466d58f0686e059735d4`. Working endings: CRLF (18 CRLF, 0 bare LF).

| Form | SHA256 of actual contents |
| --- | --- |
| working_raw | `4b959477de803fb21e3d40310318e202d72cedd654e3a68d42e869c0f4f8c2ff` |
| working_LF | `dbf27fd638a53c1df97d75447184e8c9a7ac8ec838d44caef812709a56945d12` |
| index_contents | `dbf27fd638a53c1df97d75447184e8c9a7ac8ec838d44caef812709a56945d12` |
| HEAD_contents | `dbf27fd638a53c1df97d75447184e8c9a7ac8ec838d44caef812709a56945d12` |

Expected matches: none of the four forms. Raw working=HEAD: False; LF working=LF HEAD: True.

HEAD blob also equals the family-baseline creation commit blob.

Verified exact mixed-newline reconstruction matches expected SHA and normalizes back to HEAD.

### tools/analyze_text_slot_style_fields.py

Expected: `d19a4a2345209c023c763860eba8f9c0191582616c9490aca23c8695079b30f2`. Working endings: LF (0 CRLF, 480 bare LF).

| Form | SHA256 of actual contents |
| --- | --- |
| working_raw | `b20302ec81c3775808c5f67456860cff9a07ba309ba6625ff8fef6204add002d` |
| working_LF | `b20302ec81c3775808c5f67456860cff9a07ba309ba6625ff8fef6204add002d` |
| index_contents | `b20302ec81c3775808c5f67456860cff9a07ba309ba6625ff8fef6204add002d` |
| HEAD_contents | `b20302ec81c3775808c5f67456860cff9a07ba309ba6625ff8fef6204add002d` |

Expected matches: none of the four forms. Raw working=HEAD: True; LF working=LF HEAD: True.

### tools/analyze_text_slot_spacing_fields.py

Expected: `3b2d7545189da35b9682c61575e946ea48b1cc2f4dc6fd3938ce49b9f39094b3`. Working endings: LF (0 CRLF, 544 bare LF).

| Form | SHA256 of actual contents |
| --- | --- |
| working_raw | `671c58fc4c9398c6dd1220f3390ff222ff5553c6736cc76c5ea6a6033dec2409` |
| working_LF | `671c58fc4c9398c6dd1220f3390ff222ff5553c6736cc76c5ea6a6033dec2409` |
| index_contents | `671c58fc4c9398c6dd1220f3390ff222ff5553c6736cc76c5ea6a6033dec2409` |
| HEAD_contents | `671c58fc4c9398c6dd1220f3390ff222ff5553c6736cc76c5ea6a6033dec2409` |

Expected matches: none of the four forms. Raw working=HEAD: True; LF working=LF HEAD: True.

## Historical provenance and exact reconstruction

### Chain parser

Path: `src/type3_clipboard_codec/parsers/type3_chain_parser.py`.
The latest source change is `6aee48e8e89dc57034218077e94c98ba4384582b`
(2026-09-07 20:43:07 +0900), before the first style baseline commit
`4e5dcbe1a53ca378c7130e87e5859882cef94486` (2026-09-07 21:38:52 +0900).
The later family baseline was committed as
`5174695` (2026-09-08 23:42:27 +0900).
The chain blob at both baseline commits is byte-identical to HEAD.
Thus the frozen check is not expecting an earlier *committed textual revision*.

Exact in-memory reconstruction from HEAD:
use LF endings on **1-based lines 54–55 and 289–300**, CRLF on all other lines.
There are 14 LF and 801 CRLF line endings. SHA256 becomes exactly
`9eed3128222722ca9300e3a3845600026c6562aec951c04772f86d22d03f9dbb`.
Normalizing this reconstructed byte stream returns HEAD bytes.
This proves newline differences suffice; it does not prove which editor produced them.

The nearby prior commit adds an import and the bounded slot-candidate block:
```diff
@@ imports
+from .text.text_slot_candidate import extract_text_slot_candidate
@@ after existing parsing
+        # All existing parsing is complete. This evidence has no semantic consumer.
+        paragraph_nodes = [node for node in all_nodes if node.header.class_name == "CParagraphe"]
+        slot_candidate = extract_text_slot_candidate(node.payload for node in paragraph_nodes)
```
This is historical context, **not a current working diff**. No giant-parser repair is indicated.

### Clipboard adapter

Path: `src/type3_clipboard_codec/adapters/win32_clipboard.py`.
Latest source change: `6cd781f81be3b73ed950da7a3cc6ef1cf9513ce3`
(2026-05-21 14:24:02 +0900), adding TypeEditZoneVersion support.
Previous revisions are `024daba` and `85edda7`.
The HEAD blob equals the blob at the September family-baseline commit.
All three recorded revisions were checked as raw, LF and uniform CRLF; none
matches expected `8b3b5ebf36498f5a8e7610528c2100b20ee506c2f6e468d89ed46005ebb3157c`.
Simple BOM/final-newline variants and bounded mixed-ending reconstructions around
the last commit's insertion hunks also did not match.

Consequently:
- current working vs HEAD difference is newline-only;
- a post-baseline committed source change is not the explanation;
- the exact baseline byte representation has not been recovered;
- it would be unsafe to label the mismatch an adapter behavior regression or
  to declare it definitively newline-only relative to the unknown frozen preimage.

Recover the original snapshot/generation environment or independently review its
capture provenance before authorizing a new adapter baseline. No adapter execution
or real clipboard operation was used to investigate this source.

### Additional masked package-source failure

`src/type3_clipboard_codec/models/__init__.py` also mismatches the 46-file baseline.
The test's earlier adapter assertion masks it. Its HEAD blob also equals the blob
at the family-baseline commit; latest source change is `516b4e1` (2026-05-07).
Exact reconstruction: LF on 1-based lines **1–6 and 12–18**, CRLF on **7–11**.
This yields `74dfe83ee7f2b7b5b59249c782cb4092724f2fa4cdff466d58f0686e059735d4`.
Again, normalized reconstructed text equals HEAD.

### Intentional analyzer changes and latent stale expectations

`test_text_maximum_length_cli.py:203–213` hashes both analyzers after hashing the
current slot source and chain parser. The chain failure stops the loop first.
- Style expected `d19a4a2345209c023c763860eba8f9c0191582616c9490aca23c8695079b30f2`
  matches the CRLF representation of the pre-promotion source at `4e5dcbe`.
- Spacing expected `3b2d7545189da35b9682c61575e946ea48b1cc2f4dc6fd3938ce49b9f39094b3`
  matches the LF blob at `82089a1`.
- HEAD `333d59b` intentionally adds 36 style-analyzer lines and four spacing-analyzer
  lines under the user's evidence-only task. Existing tests and old SHA constants
  were not updated. This is a real source delta, not a newline explanation.
- The new 16 tests validate additive metadata and preservation of old report values,
  null typed widths, candidate/raw behavior, RGB projection and parser decisions.

It is therefore incorrect to say **all** frozen assertions are unrelated to archive
metadata. The observed ten failures are unrelated to the additions, but two later
source assertions explicitly freeze the changed analyzer bytes.

## Assertion inventory and readiness dependencies

All fixed-source assertions below hash **raw `read_bytes()`**, not normalized text.
The complete source/expected pairs appear in the next inventory table. S = style
runtime JSON (4 entries); F = family-shadow JSON (46 entries).
Historic v1 source keys refer to `src/.../text_slot_candidate.py`, but replay replaces
that file with `tests/frozen_text_slot_candidate_v1.py`; migration explicitly hashes
the frozen file for that key. They must not be compared to v2 as if it were an error.

| Assertion consumer | Target/expected source | Readiness role |
| --- | --- | --- |
| tests/text_slot_v1_replay.py:32, historical_root | frozen v1; F slot-source entry | Import/collection gate for shadow, prefix-redesign, style CLI tests |
| tests/integration/test_text_slot_style_fields_cli.py:117–119 | all S entries in historical root | Direct source preservation |
| tests/integration/test_text_slot_prefix_redesign_cli.py:252–254 | all S entries in historical root | Direct source preservation |
| tests/integration/test_text_slot_family_shadow_cli.py:61–68 | all F entries in historical root | Source equality, runtime equality, no warnings |
| tests/integration/test_text_slot_candidate_v2_migration.py:183–185 | all F entries; v1 key mapped to frozen source | Exact historical corpus/source preservation |
| tests/integration/test_text_slot_spacing_fields_cli.py:148–153 | v2 slot source, chain source | Direct preservation; helper called again by ratio test |
| tests/integration/test_text_maximum_length_cli.py:203–213 | v2 slot source, chain source, two analyzers | Direct preservation; final analyzer checks currently masked |
| tests/integration/test_text_maximum_length_numeric_cli.py:178–182 | v2 slot source, chain source | Direct preservation |
| tests/integration/test_text_maxlength_boundary_cli.py:190–197 | v2 slot source, chain source | Direct preservation |
| tools/analyze_text_slot_family_shadow.py:519–520 | all F entries | all(...) sets source_equal |
| tools/analyze_text_slot_family_shadow.py:538–539 | source_equal | Adds sole observed warning: Runtime source hash disagreement |
| tools/analyze_text_slot_family_shadow.py:584–588 | source_equal and no warnings, plus other gates | Controls ready / not_ready |
| tests/integration/test_text_slot_family_shadow_cli.py:89 | derived readiness | Expects ready_for_review |

Other `sha256` occurrences in tests hash fixtures, structured outputs, or before/after
snapshots rather than fixed source expectations. Examples: prefix-framing,
record-schema, run-framing and color-semantics tests take before/after raw hashes;
the new archive evidence test hashes input captures. These do not introduce another
fixed-source baseline. JSON report summaries of past source_equal=true are historical
observations, not new assertion constants.

## Ten-failure classification (isolated diagnostic run)

| # | Test | Classification | First failing condition |
| --- | --- | --- | --- |
| 1 | test_text_maximum_length_cli::test_sources_and_policies_unchanged | direct frozen hash | chain parser |
| 2 | test_text_maximum_length_numeric_cli::test_source_fixture_preservation | direct frozen hash | chain parser |
| 3 | test_text_maxlength_boundary_cli::test_runtime_preserved_and_policy | direct frozen hash | chain parser |
| 4 | test_text_slot_candidate_v2_migration::test_exact_corpus_and_unchanged_other_sources | direct frozen hash | clipboard adapter |
| 5 | test_text_slot_family_shadow_cli::test_all_runtime_outputs_and_source_bytes_unchanged | direct frozen hash | clipboard adapter |
| 6 | test_text_slot_family_shadow_cli::test_challenges_and_readiness | derived readiness | source_equal=false / warning |
| 7 | test_text_slot_prefix_redesign_cli::test_current_runtime_source_unchanged[chain] | direct frozen hash | chain parser |
| 8 | test_text_slot_spacing_fields_cli::test_runtime_source_and_hashes | direct frozen hash | chain parser |
| 9 | test_text_slot_spacing_fields_cli::test_ratio_support_and_terminal | direct frozen hash through shared assertion helper | chain parser |
| 10 | test_text_slot_style_fields_cli::test_runtime_source_and_anchor_pipeline_unchanged[chain] | direct frozen hash | chain parser |

Totals: **9 direct SHA failures (7 chain, 2 adapter); 1 derived readiness failure;
0 observed independent behavioral failures** among these ten.
The models initializer and analyzer hashes are masked additional mismatches, so
fixing the first failing assertions would not by itself make the suite green.

A separate read-only report evaluation using the project's existing historical
replay produced:
```json
{"real_fixtures":104,"runtime_outputs_equal":true,"runtime_source_equal":false,
 "warnings":["Runtime source hash disagreement"],"readiness":"not_ready"}
```
The existing historical replay is necessary: directly mixing a historical analyzer
with the current v2 import in one process raises the known prefix_variant mismatch.
The final diagnostic used the existing replay_parser context, not a new parser fix.

## Test accounting

Interpreter explicitly requested and used:
`C:\work\develop\type3-clipboard-codec\.venv\Scripts\python.exe`, Python 3.14.7.
The IDE environment query still returns the unrelated TypeEdit SDK; no interpreter
or package configuration was changed.

Commands used `PYTHONPATH=src`, `PYTHONDONTWRITEBYTECODE=1`,
`python -B -m pytest -q -p no:cacheprovider --tb=short`.
The focused run additionally selected the new archive-metadata test file.

| Run | Collection errors | Executed test items | Passed | Failed | Skipped | Xfailed | Xpassed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Original checkout full suite | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| Isolated diagnostic copy full suite | 0 | 1196 | 1186 | 10 | 0 | 0 | 0 |
| Focused archive metadata tests, original checkout | 0 | 16 | 16 | 0 | 0 | 0 | 0 |

Original run: 0.37 seconds. Isolated run: 79.06 seconds. Focused: 2.12 seconds.
A collection error is not an executed test failure or a not-registered runtime event.

Diagnostic copy:
`C:\Users\USER\AppData\Local\Temp\type3-frozen-baseline-diagnosis-cea7283652574515b7fa5d1e13883d13`.
Only the frozen-v1 source and current-v2 slot-source newline representation was
converted to LF **in that disposable copy**, reproducing the earlier diagnostic
setup. It was not an all-files LF normalization, nor a repository repair. Existing
historical replay creates its own temporary root for relevant CLI suites.
Neither expected hashes nor test code was changed. No claim of full-suite success.

## Repair options — not executed

Every repair below requires separate human authorization; this task authorized
diagnosis only.

| Option | Proposed change | Risk / snapshot protection | Recommendation |
| --- | --- | --- | --- |
| A: restore parser/adapter from HEAD | Rewrite working files from identical committed text | No substantive fix; autocrlf can recreate same failing bytes; needless rewrite | Do not do this |
| B: explicit LF policy for exact frozen/v2 snapshots | Future checkout/attribute or dedicated immutable-fixture policy for the two proven LF snapshots | No hash weakening if exact existing expected bytes are restored; narrow fix for collection and v2 raw hash only | Smallest independently justified first repair; does not close other failures |
| C: verified canonical source integrity for chain/models | Preserve historical raw hashes and their exact reproduced byte evidence; review a separately named normalized-content invariant | Prevents newline-only failures while preserving code-text protection; normalization intentionally stops protecting line-ending bytes | Consider only with explicit policy approval; never silently replace raw hashes |
| D: adapter baseline reconciliation | Recover original snapshot or capture-time source; compare with committed text and behavior before adopting any canonical baseline | Unknown preimage currently prevents certifying pure normalization; blind replacement would weaken protection | Block hash update until provenance is resolved |
| E: analyzer preservation contract | Keep pre-promotion reference and independently verify exactly the approved additive delta / old output invariants | Legitimate code change needs explicit scope-aware protection; whole-file old SHA cannot remain an invariant for edited files | Separately approve a narrow test update; no blanket source-hash rebaseline |
| F: separate readiness signals | Retain source-integrity gate, report behavioral equality and snapshot-byte mismatch separately | Better diagnostics; dropping source_equal from readiness would weaken existing protection | Reporting separation only; do not bypass the gate |

Do not update an expected SHA merely because current code hashes differently.
The safest immediate repair scope is the exact LF snapshot checkout issue, followed
by an explicitly reviewed source-integrity policy. Adapter preimage recovery and
analyzer-contract reconciliation are distinct follow-ups. A single autocrlf toggle
or all-files LF rewrite would break baseline entries that intentionally match CRLF.

## Acceptance answers

1–6. Exact paths, expected hashes and all four measured hashes are in the hash matrices and appendix.
7. Frozen v1 and v2 match LF/index/HEAD; chain/models match only the documented mixed-ending reconstructions; adapter matches none of the reviewed forms; analyzers match older revisions only.
8. Working-vs-HEAD differences are newline-only for production affected files. Relative to expected snapshots this is proven for chain/models/v1/v2, unresolved for adapter, and false for the intentionally changed analyzers.
9–10. Applicable attributes are unspecified; system core.autocrlf=true; no local override.
11. HEAD itself does not reproduce all frozen raw baselines; this incompatibility existed at baseline capture for chain/models/adapter. The v1/v2 LF blobs do match their applicable expectations.
12. No uncommitted actual source edits at investigation entry. The prior authorized metadata changes are committed.
13. Exactly one of ten failures is derived readiness; nine directly compare source SHA.
14. None of the observed ten failed assertions is caused by archive metadata values. The two old analyzer SHA checks are nevertheless stale because of that authorized change and currently masked.
15. The focused sixteen tests pass under project Python 3.14.7.
16. baseline_status=multiple_causes.
17. Smallest justified first repair: restore explicit LF snapshot consistency under a separately approved policy, without changing expected hashes. This alone will not make all tests pass.
18. Do not blindly change expected SHA; adapter provenance is still missing, and canonicalization/authorized analyzer deltas need separate review.
19. Focused metadata invariants and observed runtime-output comparisons pass. Do not certify the implementation globally regression-clean while source-integrity checks remain unresolved.
20. Do not resume parser/promotion implementation under a green-baseline claim. Preserve the completed evidence-only implementation; repair/reconcile baseline integrity before treating full regression readiness as restored.

Only this report is added to the repository. No production source, adapter, parser,
test, fixture, previous report, Git attribute/configuration or frozen expected SHA
was modified; no additional promotion or runtime vendor/clipboard investigation occurred.


## Appendix: complete fixed-source expected-value inventory

S and F are the two JSON baselines identified above; their consumers and raw-byte mode are listed in the assertion table. The four S entries are a subset of F, not four additional distinct source targets. Historical slot keys are mapped to frozen v1 where indicated by the test.

| Target source key | Baseline membership | Expected SHA256 | Historical working-form result |
| --- | --- | --- | --- |
| src/type3_clipboard_codec/parsers/type3_chain_parser.py | S/F | `9eed3128222722ca9300e3a3845600026c6562aec951c04772f86d22d03f9dbb` | exact mixed endings reproduce expected |
| src/type3_clipboard_codec/parsers/text/text_slot_candidate.py | S/F | `76458eecec602b6e41f97c06b7188723fcf7a53e0bec1fe99445a586625d7d28` | LF matches (frozen v1) |
| src/type3_clipboard_codec/parsers/text/text_pipeline.py | S/F | `ff6745a89de61fa85d4187fb2b80d632154ca5f738f46a87de25080356289503` | raw matches |
| src/type3_clipboard_codec/parsers/text/cparagraphe_parser.py | S/F | `65f94c639049ad8cfce1374c8933b51c5f0d6f8b214adbe285b17c07d2dd9133` | raw matches |
| src/type3_clipboard_codec/__init__.py | F | `7ded14d133b560f68c960f0ec92f6bc9d052dbde0c373b86d42be57c571a902f` | raw matches |
| src/type3_clipboard_codec/adapters/input_base.py | F | `d0a22f7f6b195c8ff01c27f0ce721d9ff0fb5f59df9abe65e193b6975cbe0183` | raw matches |
| src/type3_clipboard_codec/adapters/manual_hex_input.py | F | `c567b48f7a261b76e45d56efc0ad9541150dd491f3ce284724c4badb10a09c5f` | raw matches |
| src/type3_clipboard_codec/adapters/win32_clipboard.py | F | `8b3b5ebf36498f5a8e7610528c2100b20ee506c2f6e468d89ed46005ebb3157c` | preimage unresolved |
| src/type3_clipboard_codec/codec/__init__.py | F | `ff2906abfa31464c775c96d530c9e5bd71b5f9297c269aff5d55ff60f54348d0` | raw matches |
| src/type3_clipboard_codec/codec/decoder.py | F | `41489dd1ecfcb1d07be911908bc915ce2a11017a3d7821b78fcbcb3a2aa7c74b` | raw matches |
| src/type3_clipboard_codec/codec/encoder.py | F | `04984d33c6bbe8a251df1ea881924b3c66cfefa89ec94a1b395b96448eec207f` | raw matches |
| src/type3_clipboard_codec/codec/preview.py | F | `2e32f21e9e374d989ae7404ee6bce70961be4f3ba3ad97bf74bb1f99553c55cd` | raw matches |
| src/type3_clipboard_codec/exceptions.py | F | `e91f75fbec05243151c2b8c708a138ad4352f03cef155d01cd4311cd02325bcb` | raw matches |
| src/type3_clipboard_codec/inspect/__init__.py | F | `2aed9d44643c35a380a9bb29bf699a5f08baab287b4f493e223bc3b7932536ac` | raw matches |
| src/type3_clipboard_codec/inspect/formatters.py | F | `c4e9a0b2fd5a0e8b2e02d03162222b7082ba52591e5b4c7b440518e0392d7921` | raw matches |
| src/type3_clipboard_codec/inspect/hex_input.py | F | `f68c701f26d8dca4b3855cf8194586f32d795afd94f90b40f26c60a1402aecea` | raw matches |
| src/type3_clipboard_codec/models/__init__.py | F | `74dfe83ee7f2b7b5b59249c782cb4092724f2fa4cdff466d58f0686e059735d4` | exact mixed endings reproduce expected |
| src/type3_clipboard_codec/models/colors.py | F | `b7ef8b67ca8a0720070c9d7836595aeb62090f6eedb80fe2fa1512ca8868bbbe` | raw matches |
| src/type3_clipboard_codec/models/geometry.py | F | `f08836e3155175e5be7b1bc9e52d4d4a2842ce1fabd2d1befe4cc028832bd259` | raw matches |
| src/type3_clipboard_codec/models/parsed_object.py | F | `b794ed0be5b99076eb51d5f4129b6eb659c03f8d2508a2854c4c6d37561b5c65` | raw matches |
| src/type3_clipboard_codec/models/text_object.py | F | `f712aa6954b75a0025870fb16abe3b0485597b1792d74e191dd155cf976139a4` | raw matches |
| src/type3_clipboard_codec/parsers/__init__.py | F | `48e03662007937a20db1e7303588f7fd5e33ad26e96bc50f8db71b226088900e` | raw matches |
| src/type3_clipboard_codec/parsers/base.py | F | `fe40a0419c0b1990fe98da3731827281ecce4749d63f1e75e220d189a4732ce4` | raw matches |
| src/type3_clipboard_codec/parsers/binary/__init__.py | F | `f178f1d50f866ba3df118cf8564a31f6dbd401332f6d0a99554a6bab02b22380` | raw matches |
| src/type3_clipboard_codec/parsers/binary/header_parser.py | F | `918480df5bdfc71903ec96408408b6d5b9f9b64264f05cda2d9ecfeccefbfede` | raw matches |
| src/type3_clipboard_codec/parsers/binary/node_parser.py | F | `b345d4707f0a75fb6c1eee4d75fc0779e6d91bd5249057f98a45d38ce4ad9bad` | raw matches |
| src/type3_clipboard_codec/parsers/binary/node_scanner.py | F | `335fe32e0b846a2db16b7c8f6e37c1fecbd7cd225b73c473ad3f5c777d1d9cb5` | raw matches |
| src/type3_clipboard_codec/parsers/common.py | F | `3df65c47c8a39816b667562166e7c37ffcaa6c92d77dc53ef2dcc7f4fb082931` | raw matches |
| src/type3_clipboard_codec/parsers/geometry/__init__.py | F | `b54ef95e41199d340f317b02ac157c06b0b4ea71fbf136dd7424ac1f5e521261` | raw matches |
| src/type3_clipboard_codec/parsers/geometry/chain_builder.py | F | `9d4147af5f5cd1f95473be0c37c76747268b18d3e8d76a0250c90c06937c408f` | raw matches |
| src/type3_clipboard_codec/parsers/geometry/contour_candidate_ranker.py | F | `da8eb3fddbe9f17acbb427dc030a5948646143a1bd925b2e0aa824092458c40b` | raw matches |
| src/type3_clipboard_codec/parsers/geometry/contour_candidate_validator.py | F | `61c83ac7e65fce05a20ccd69a6e2f167ecf63d5b6a8dc759b858c5593d9954cb` | raw matches |
| src/type3_clipboard_codec/parsers/geometry/contour_parser.py | F | `2e2393fe9cf1c7e4aea3cdaf2a5ee6dd214c07f42a4a31a9e64f97381cfde862` | raw matches |
| src/type3_clipboard_codec/parsers/geometry/shape_classifier.py | F | `1df04e398b47112b0c99d929f2c5391099e2ba7ce611150e964bafebd0ad2f64` | raw matches |
| src/type3_clipboard_codec/parsers/object_detector.py | F | `fa4451535646d9edc115e532f7296f651d056d329433809138730f44d8e58ac1` | raw matches |
| src/type3_clipboard_codec/parsers/registry.py | F | `d5c81d5bb78ad5fd487e8c95c23be3a5490c14b9747e38126ac10b740690fceb` | raw matches |
| src/type3_clipboard_codec/parsers/style/__init__.py | F | `20560e46f293c97ecc7861ba457d3b0bb7f6fd7100c4ac0508207b76738e484a` | raw matches |
| src/type3_clipboard_codec/parsers/style/property_extend_parser.py | F | `6f0e9a80d8802c61becea5cdaee5b40710f10f68fe07c6ba6e81398abbbeaa21` | raw matches |
| src/type3_clipboard_codec/parsers/text/__init__.py | F | `7d5748fe06593b049b13b5a670399defdda2119cf3e0f6b55651ef052192e65f` | raw matches |
| src/type3_clipboard_codec/parsers/text_parser.py | F | `9cb37b272d52eff2b80914c2281f98e1728b721d79ae7ddd93a6c169a350c2b3` | raw matches |
| src/type3_clipboard_codec/parsers/unknown_parser.py | F | `408b62a65ae82fe183f83bd6dc15692aa33b398a9bf324249ea0f1a2f6726966` | raw matches |
| src/type3_clipboard_codec/services/inspect_service.py | F | `c6a50cf3b53c8a4d2a7a3296b8a8c74045bfca83e14b18e6e906343defbbab8f` | raw matches |
| src/type3_clipboard_codec/utils/__init__.py | F | `d8b47acf872628fb5eaef92879c08bbb4980d1d7af57bd8138dafe924706480a` | raw matches |
| src/type3_clipboard_codec/utils/ascii_scan.py | F | `af2993a4b31c459ee6eb11ad9636bab8ea887df242e25bb739938ec6a2b894ea` | raw matches |
| src/type3_clipboard_codec/utils/bytes_reader.py | F | `9bbc847b5356c6100b57980bd647e2a16d42a225b84b2d3ecdfa24d5fb81dfef` | raw matches |
| src/type3_clipboard_codec/utils/hex_text.py | F | `dc486df3ccc87f6686e42e599f9817740148b32e6b0d5657951f82e87ac54d6c` | raw matches |

Additional hard-coded assertions (all raw bytes):

| Target | Expected SHA256 | Consumers |
| --- | --- | --- |
| src/type3_clipboard_codec/parsers/text/text_slot_candidate.py (current v2) | `31ff8567fe65c08ff9085d5433b1b533efc6978f540b6ed0d17dd735dba00876` | spacing:150, maximum:205, maximum numeric:179, boundary:193 |
| src/type3_clipboard_codec/parsers/type3_chain_parser.py | `9eed3128222722ca9300e3a3845600026c6562aec951c04772f86d22d03f9dbb` | spacing:151, maximum:207, maximum numeric:181, boundary:195; same value as S/F |
| tools/analyze_text_slot_style_fields.py | `d19a4a2345209c023c763860eba8f9c0191582616c9490aca23c8695079b30f2` | test_text_maximum_length_cli.py:211–213 (masked) |
| tools/analyze_text_slot_spacing_fields.py | `3b2d7545189da35b9682c61575e946ea48b1cc2f4dc6fd3938ce49b9f39094b3` | test_text_maximum_length_cli.py:209–213 (masked) |


## Approved canonical source-integrity policy

This section records the subsequently authorized policy migration. The diagnosis
above remains historical evidence; its raw-byte failure status is not erased.

Python source snapshot integrity now uses `tests/source_integrity.py`:
read bytes, replace CRLF pairs with LF, then SHA256. Bare CR, whitespace, tabs,
encoding, Unicode byte sequences and final-newline presence are preserved.
The path-level API rejects non-`.py` artifacts. This helper is test/diagnostic
support, not production codec functionality.

Fixtures, clipboard captures, serialized payloads, binary/vendor evidence,
JSON golden outputs and before/after byte-preservation checks remain raw-byte
protected. Nothing under `src/type3_clipboard_codec` or `tests/samples` is changed.

`tests/source_integrity_baselines.json` centralizes 49 records representing 48
distinct logical source paths; the historical slot source also has a separate
frozen-v1 file, making 49 physical paths protected across the snapshots.
It retains every original legacy raw SHA, status, reason and committed provenance:

- Historical F source text: the original family-baseline commit `5174695`.
  The four S entries are also checked to equal their earlier `4e5dcbe` blobs.
- Current v2 slot source: reviewed migration commit `a220a48`.
- Only the two analyzers move to approved archive-metadata commit
  `333d59bd32ee0aed8418edf806be9c9604e0e785`. Their legacy baselines are marked
  `superseded_by_approved_source_change`; the 16 metadata-preservation tests remain.
- Chain/models mixed endings remain historical provenance. The adapter still says
  `raw_preimage_unresolved`; its canonical expectation comes from the known
  baseline commit, without claiming recovery of unknown historical raw bytes.

The new expected digests were calculated from `git show <commit>:<path>` binary
stdout followed only by CRLF-to-LF conversion, not from working-tree content.
Runtime tests load the committed metadata file; Git is not a test dependency.

All fixed Python-source gates in the diagnosis inventory now use this helper,
including historical replay entry, S/F snapshot loops and current/analyzer checks.
The original raw SHA JSON files are unmodified and remain provenance.
Historical replay still substitutes the frozen v1 extractor and checks all 104
recorded runtime outputs. The replay copy includes the new support helper/table.

The diagnostic shadow report separates `canonical_source_equal` from
`legacy_raw_source_equal`. The existing `runtime_source_equal` key remains as
a compatibility alias of canonical equality. Canonical mismatch produces
`Canonical runtime source disagreement` and blocks readiness. Legacy-only
mismatch produces separate provenance information,
`Legacy raw snapshot byte representation differs`, and does not enter warnings.
Source integrity, runtime equality, warning constraints and all structural gates
remain required. No source check is skipped for the adapter.

No `.gitattributes`, Git setting, source encoding, parser decision or archive-type
metadata was changed. This is an explicit integrity-policy migration, not an
unconditional baseline refresh or a parser promotion.


### Migration validation and resulting status

The source-integrity baseline is **repaired under the approved canonical-source
policy**. The earlier `multiple_causes` diagnosis remains true for the historical
raw-byte policy; it is not evidence of a current canonical mismatch. The adapter's
legacy raw preimage remains unresolved provenance, not a skipped integrity check.

Acceptance used the **real original checkout** with system `core.autocrlf=true`
and project Python 3.14.7 at
`C:\work\develop\type3-clipboard-codec\.venv\Scripts\python.exe`.
The request's `type3-clipboard-codec.venv` path did not exist; the existing
project-local `.venv` above was used. No disposable LF-normalized acceptance
checkout, dependency injection or Git setting change was needed.

| Check | Result |
| --- | --- |
| New source-policy tests | 70 passed |
| Existing archive-metadata tests | 16 passed |
| Full actual-checkout suite: PYTHONPATH=src python -B -m pytest -q -p no:cacheprovider | **1266 passed**, 80.21 seconds |
| Collection errors / failed / skipped / xfailed | 0 / 0 / 0 / 0 |
| Historical 104-fixture replay | runtime_outputs_equal=true; canonical_source_equal=true; readiness=ready_for_review |
| Canonical adapter/text mutation | Integrity fails; synthetic canonical mismatch still blocks readiness |
| Legacy-only mismatch | Reported as provenance, outside warning/readiness failure |
| New helper and new tests: default Ruff | Passed |
| Changed legacy tests/support: default Ruff | 37 pre-existing diagnostics remain (I001=9, C408=19, PERF102=1, PLW1510=8); no new diagnostics |
| All changed Python: Ruff E4/E7/E9/F | Passed |
| git diff --check | Passed |
| Production src / fixtures / archive style+spacing implementation diffs | Empty |

The existing family-shadow tests were also rerun (10 passed). After the full suite,
only a superfluous blank line in that test's imports was removed for Ruff; no
behavioral code changed. There are no remaining test failures. Broad legacy Ruff
cleanup was intentionally not performed.

Raw SHA256 preservation was checked before and after, not merely Git's normalized
diff. Each aggregate hashes sorted `relative_path:raw_file_sha256` rows:
- 46 production files: `8956966a68e447c0402b72e20f49ed95fffe03a2dc6d3964c3f35f94dba95422`.
- 204 files under tests/samples: `b71e8ac36824d7876d7e0d39e8a8fc15d99dcdfe35805d37a473cbf83d6b9b30`.

Changed files in this policy migration:
- `tests/source_integrity.py`
- `tests/source_integrity_baselines.json`
- `tests/integration/test_source_integrity_policy.py`
- `tests/text_slot_v1_replay.py`
- `tests/integration/test_text_maximum_length_cli.py`
- `tests/integration/test_text_maximum_length_numeric_cli.py`
- `tests/integration/test_text_maxlength_boundary_cli.py`
- `tests/integration/test_text_slot_candidate_v2_migration.py`
- `tests/integration/test_text_slot_family_shadow_cli.py`
- `tests/integration/test_text_slot_prefix_redesign_cli.py`
- `tests/integration/test_text_slot_spacing_fields_cli.py`
- `tests/integration/test_text_slot_style_fields_cli.py`
- `tools/analyze_text_slot_family_shadow.py`
- `docs/frozen_baseline_integrity_investigation.md`

No production parser, adapter, model, fixture, original raw snapshot JSON, archive
metadata implementation or its 16 tests changed. No empty-extension work or further
semantic promotion was started.
