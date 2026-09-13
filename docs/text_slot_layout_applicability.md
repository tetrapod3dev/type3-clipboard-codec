# Production current/empty 204-byte layout gate

For current consumer-facing interpretation across the subsequent typed-output
and alias batches, use the
[text-slot typed candidate consumer contract](text_slot_typed_candidate_contract.md).

**production_204_gate_status = implemented_fail_closed**.
Support is restricted to existing structurally aligned candidates with current
**CTxtAttrChar v5 / CPropertyExtend v5 / empty extension**. Unsupported layouts
abstain. Typed parsing readiness and all semantic labels remain unchanged.

The applicability investigation below is retained as historical code/corpus
evidence. Its statements that no production gate is active describe the earlier
shadow batch; this production update supersedes that implementation status only.
Both shadow analyzers and both JSON evidence models are unchanged.

## Conditions and placement

Only `src/type3_clipboard_codec/parsers/text/text_slot_candidate.py` changes in
production. Its private pure `_validate_current_empty_slot_layout(record)` requires
an exact 204-byte window and returns a compact failure reason or `None` for success.
It imports no tool, evidence JSON, UI code or semantic parser.

| Record-relative field | Width | Required value |
| --- | ---: | ---: |
| AttrChar version, +0 | 4 LE | exactly 5 |
| Extension version, +92 | 4 LE | exactly 5 |
| Array count #1, +132 | 4 LE | 0 |
| Array count #2, +152 | 4 LE | 0 |
| String length #1, +188 | 4 LE | 0 |
| Optional zone #1, +192 | 4 LE | 0 |
| String length #2, +196 | 4 LE | 0 |
| Optional zone #2, +200 | 4 LE | 0 |

The six guards are checked in frozen archive order, stopping at the first failure.
Their offsets and the version/size definitions are immutable tuples/integers in
the candidate module. Other fixed extension bytes remain unconstrained. Neither
an all-zero extension nor `version>=5` is accepted as a substitute.

Existing token discovery, F4 classification and root calculation are unchanged.
The original 204-spaced root calculation is tentative candidate topology, not a
successful length validation. Once it identifies a unique root, the existing run
loop validates that first window **before** adding its position or advancing by
204. Each subsequent window, including the terminal record, uses the same gate.
The original count agreement and terminal/continuation checks still run before
returning a candidate. Final count agreement is not moved ahead of record validation.

Any failed record rejects the entire candidate; no partial run escapes. Truncation
maps to the existing private bounds audit, other layout failures to its private
layout audit. No public candidate keys are added. The helper does not scan bytes
for version pairs, determine ownership, skip variable data or infer another stride.

AttrChar v0-v4, extension v0-v4, unknown higher versions, negative-bit-pattern
versions, nonzero counts/lengths, and any nonzero zone presence all abstain.
No array, string or zone payload is parsed. Real nonempty extension coverage remains
**zero**; the new negatives exist only as in-memory mutations.

## Preservation and regression coverage

The regression freezes the pre-gate v2 extractor directly from the previously
committed source in `tests/frozen_text_slot_candidate_v2.py`. It uses that original
extractor to establish corpus alignment, so a new rejection cannot silently shrink
the production/shadow comparison population. Production never imports this copy.

- All **700** reviewed records pass: **616 visible, 84 terminal**.
- All 700 production decisions agree with shadow `combined_future_204_supported`.
- Full parser dataclass/chain output for **116 valid hex captures** is equal to
  both the frozen v2 implementation and the actual pre-task in-memory snapshot.
- Per-paragraph candidate dictionaries remain exactly equal, including source,
  presence, F4 family, +08, count, stride, raw/unknown bytes and terminal state.
- No archive_type_evidence, typed_width, RGB projection, callback ownership,
  Maximum Length, compression, spacing, style-field or terminal semantics change.
- F4's function text is checked for exact equality to the committed pre-gate copy.

Synthetic tests mutate both versions through 0/1/2/3/4/6/0x7FFFFFFF/0xFFFFFFFF
on first, interior and terminal records; each of six guards through positive and
invalid nonzero words on every record; all 204 proper record prefixes; meaningful
enclosing-payload boundaries; and input names/order/offsets. Whole-parser negative
tests verify candidate abstention without changing the parser chain or crashing.
A spy on validation confirms first-record failure stops before any stride advance.

Existing valid synthetic run builders now emit the reviewed extension version
and guards while preserving arbitrary nonzero opaque fields. Their exact token
and probe budgets account for the additional version token in each record.
Three existing shadow/metadata test locations formerly asserting nonempty/legacy
production acceptance now assert rejection; their shadow and metadata assertions
remain. No shadow evidence was changed to force agreement.

## Canonical source provenance

Production commit: `4836b5a37bcfb21570b995d011905c4cfdfe57ad` (local; no push).
Its only file is the candidate implementation. The one current source-integrity
record now names this commit and blob `9b26098cf6f257594af3b5c0294dc8ccbaae3a12`.
Canonical SHA256, computed with `tests/source_integrity.py` from binary
`git show <commit>:<path>` output, is:
`f5c976698d519dc725dc03412f5e6026b0a71c8c8312a6da60d24f5f430206d2`.

The prior complete canonical/commit/legacy record is retained in
`previous_baselines`; its canonical SHA remains
`31ff8567fe65c08ff9085d5433b1b533efc6978f540b6ed0d17dd735dba00876`.
Legacy raw SHA is unchanged and status records `superseded_by_approved_source_change`.
The reason is explicitly approved production current-layout gate. Every other
baseline record and group membership is identical; there is no blanket rebaseline,
historical output regeneration, policy bypass or dirty-tree-derived expectation.

## Actual checkout validation

Validation uses `C:/work/develop/type3-clipboard-codec/.venv/Scripts/python.exe`,
Python 3.14.7. The supplied path lacking the separator before `.venv` does not
exist; IDE lookup still returns the other open project's Python 3.12.

| Check | Result |
| --- | --- |
| New production-gate tests | 29 passed |
| Existing applicability tests | 36 passed |
| Existing empty-extension tests | 26 passed |
| Archive metadata tests | 16 passed |
| Historical replay | 1 passed; 104 fixtures, runtime_outputs_equal=true, canonical_source_equal=true, readiness=ready_for_review |
| Existing migration challenge regression | 1 passed |
| Combined focused run | **109 passed in 15.16s** |
| Full actual checkout: `PYTHONPATH=src python -B -m pytest -q -p no:cacheprovider` | **1357 passed in 88.04s**, baseline 1328 + 29 |
| Default Ruff on all changed/new Python | 14 inherited diagnostics (C408=12, I001=2); zero newly introduced diagnostics against pre-gate committed code |
| Ruff E4/E7/E9/F | Passed |
| `git diff --check` and new-file whitespace checks | Passed |
| Fixture inventory/raw SHA256 | 204 before and after; zero mismatches |
| Tools/shadow evidence and chain-parser diffs | Empty |
| Production diff versus pre-task commit | One candidate file only, 36 additions / 1 replacement |
| Baseline scope audit | 1 of 49 source records changed; group membership unchanged |

The default Ruff findings are retained source-style issues, including the exact
pre-gate snapshot's inherited C408. New production/test logic adds no diagnostics;
unrelated source cleanup was not mixed into the structural gate.

Modified production file: `src/type3_clipboard_codec/parsers/text/text_slot_candidate.py`.
Other files: this document, `tests/source_integrity_baselines.json`, new
`tests/frozen_text_slot_candidate_v2.py` and
`tests/integration/test_text_slot_current_empty_gate.py`, existing applicability,
empty-extension, archive-metadata and v2-migration integration tests, and the two
candidate unit-test modules. Historical v1 source/runtime outputs and all evidence
captures remain immutable. The migration challenge still verifies the original
count/terminal failure using frozen v2, then verifies the new earlier layout veto.

There is no remaining implementation blocker for this reviewed current/empty gate.
Nonempty extensions, alternate versions, global MFC schema decoding and typed
semantics remain unsupported or independently unready; this batch does not start
those tasks. All checks ran against the actual checkout, with no skips or xfails.

---


# Text-slot current serializer applicability investigation

**serializer_applicability_readiness = ready_for_production_gate_review**, scoped
to the existing structurally aligned AttrChar candidates and the reviewed vendor
serializer family. No production gate is activated; every shadow output retains
`parser_safe=false`. This is not a universal class-identification rule for arbitrary
bytes and does not widen the five-fixture exact internal crosswalk.

The missing discriminator is **CPropertyExtend's serialized version at record+92**.
Together with AttrChar's version at record+0, exact equality to **5 / 5** establishes
the reviewed current version path. Both fields occur before any variable emission.
The earlier empty-extension investigation's statement that extension member+4 was
not yet proved a version remains historical evidence; its files and outputs are
unchanged. Reading the load branches now establishes that role directly.

## Code-first evidence and frozen positions

Read-only evidence includes the seven scoped Serialize CFGs listed in
[the version manifest](../tools/text_slot_layout_version_evidence.json), the
[current-store operation model](../tools/text_slot_empty_extension_layout.json),
[Phase 2D origin report](C:/TypeEdit_2009_reverse_engineering/reports/phase2d_c_origin_resolution.md),
and [Phase 3 review](C:/TypeEdit_2009_reverse_engineering/reports/phase3_codec_promotion_review.md).
The existing exact internal crosswalk supplies provenance only. The analyzer never
uses C+310, absolute raw coordinates, fixture identity, intended text/color/style,
attempt order, or final parser order to find records.

Additional static PE inspection was restricted to directly relevant
CPropertyExtend constructors and CCaractere/CParagraphe ResetVersion/runtime-class
records. Vendor code was never executed, loaded, patched, or captured anew.

- MaudeTxt.dll SHA256: `0e03417d95bcb0168ad876a6ea77be6b51d47ebaa49bf63a3d1298d7c3a1a621`.
- Maude.dll SHA256: `eded4261fe6df1f22ceb098648188a6d789c1b6eed5a713a97e0e0e52a895f91`.

| Marker | Exact archive order / width | Current value and evidence | Runtime classification |
| --- | --- | --- | --- |
| AttrChar version | first emission, record+0, 4 bytes LE | literal 5 assigned 4D7B1, written 4D7B9, read 4D892 | exact_local |
| Extension version | first extension emission, record+92, 4 bytes LE | member+4 written 603B2; read to local at 605F4 and compared at 605F9/60627/6063B/606EB/60756 | exact_local |
| AttrLine version | first AttrLine emission, 4 bytes LE | literal 4, write 4DE17/read 4DE97 | requires_parent_context |
| AttrPara version | first AttrPara emission, 4 bytes LE | literal 4, write 4E212/read 4E27E | requires_parent_context |
| CTxtPara own version | no emission, width 0 | first bytes belong to embedded AttrPara, not CTxtPara | not_serialized |
| CTxtAttrStyle own version | no emission, width 0 | direct Char, Line, Para virtual calls | not_serialized |
| CParagraphe class/schema state | no own payload version word | cached m_iVersion; archive ordinal3051 on first load | requires_parent_context; full schema resolution unresolved |
| CCaractere class/schema state | no own payload version word | cached m_iVersion; archive ordinal3051 on first load | requires_parent_context; not a repeated slot |

The extension constructor at Maude.dll RVA **5FF50** assigns member+4=5 at
**5FF83** (`c7 46 04 05 00 00 00`). Its copy constructor at 5FFF0 copies that
member at 60064/60067. Store writes the member, not a literal: consequently the
analyzer must read the actual bytes even for an AttrChar v5 record. Load does not
overwrite the object's member+4 with the incoming version; it branches on a local.
No ResetVersion global is consulted in AttrChar/Line/Para/Style/CTxtPara or this
extension serializer. No additional serialized feature flag selects another v5
layout in these routines.

The fixed AttrChar emission sum is the already frozen 5*4+9*8=92. Extension entry
is the call at 4D882, after that sum. Therefore the extension version is at +92
without assuming its extent, counts, string lengths, presence flags, or a 204-byte
stride. These two positions were fixed before the corpus comparison.

## Current versus legacy map

All sizes include their local version word. Version comparisons in the loaders
are signed. "Accepted" below means a branch consumes bytes; it does not mean the
vendor validates the value. The shadow accepts only exact reviewed current values.

| Serializer | Current store | Load-side branch behavior | Size consequences |
| --- | --- | --- | --- |
| AttrChar | 5 | v1 special packed-flag conversion; v>=2 common path; >=3 adds DWORD+54; >=4 adds double+58; >=5 calls extension; other signed values below 2 consume only version | v1=72, v2=80, v3=84, v4=92, v5=92+E |
| AttrLine | 4 | v<4 converts flags; >=2 adds double+10; >=3 adds DWORD+40; >=4 adds double+18 | v1=48, v2=56, v3=60, v4=68; signed <2 follows 48-byte path |
| AttrPara | 4 | common 24; >=2 adds double+18; >=3 adds two doubles+20/+28; >=4 adds DWORD+30 | v1=24, v2=32, v3=48, v4=52; signed <2 follows 24-byte path |
| CPropertyExtend | member+4, default 5 | cumulative thresholds >=1, >=2, >=3, >=4, >=5 | empty v<1=4, v1=20, v2=24, v3=52, v4=64, v5=112 |
| CTxtAttrStyle | no own version | same ordered virtual delegation in store/load | Char+Line+Para; current empty total 324, not 204 |
| CTxtPara | no own version | AttrPara, DWORD line count, typed Line list, DWORD char count, typed Char list | prefix depends on actual Line versions/count; no wrapper class/schema bytes per list element |
| CParagraphe | current store unconditional | cached state<5 calls readOldVersion B030; explicit v4 branch B93F; >=5 current; >=6 adds final DWORD | complete old prefix remains unresolved; current schema 5 omits final 4 bytes compared with 6 |
| CCaractere | current store unconditional | load cached state==3 current; every other state enters raw legacy conversion | after CCourbe base, legacy raw reads total 388; current has four vector serializers and embedded AttrChar; not a slot-size rule |

AttrChar v1 lacks member+48, +54, +58 and extension; v2 adds +48, and v3/v4
add the fields above. All v1-v4 omit **all six** extension empty guards.

Extension v1 adds +10:8, +8:4, +18:4; v2 adds +1C:4; v3 adds four DWORDs,
array30 count/data and two DWORDs; v4 adds +40:8 and array48 count/data; v5 adds
four 8-byte fields and string50/zone54/string58/zone5C. Thus the first array count
exists from v3, the second from v4, and both string-length and zone-presence words
only from v5. The v5 optional encoding is DWORD presence followed by direct virtual
CZone::Serialize; no WriteObject framing is emitted at these calls. v<5 has no
such optional-zone fields. Nonempty nested CZone internals need not be parsed for
an empty-only gate and were not broadened into this investigation.

None of these threshold-based attribute/extension loaders rejects future high
versions. Treating `>=5` as current would therefore be unsafe. The shadow rejects
0, negative-bit-pattern values and unknown higher versions as `unsupported_version`;
known positive lower versions become `legacy_or_other_layout`. Extension v0 is a
visible load branch but is deliberately unsupported, never current.

## Parent context and schema limits

CParagraphe::ResetVersion 6D00 clears global RVA7FA24; CCaractere::ResetVersion
13D0 clears RVA7F2D0. Their first-load calls to ordinal3051 populate those globals
at BCDC and 1945 respectively. Static runtime-class metadata contains version-shaped
words 0x80000006 for CParagraphe (record RVA79260), 0x80000003 for CCaractere
(79000), and 0x80000005 for CPropertyExtend (Maude FFBCC). These PE metadata words
are not extra inline words emitted by the inspected Serialize calls. The exact
archive ordinal name and global MFC class/reference schema resolution remain
unpromoted. A parser field named `class_id` is not proof of that mapping.

**Minimum additional parent bytes required for the local version conjunction: none**,
given the existing structurally aligned AttrChar candidate precondition. Neither
AttrChar nor extension dispatch uses a parent version global. Their explicit local
versions decide the reviewed layouts. A parent value cannot rescue a noncurrent
local version. Anonymous bytes containing 5/5 do not independently prove the
class identity or establish an object boundary.

For separately supplied CTxtPara entry P, current prefix order gives:

- AttrPara version: P+0; current AttrPara length 52.
- Line count: P+52, DWORD.
- Line i version: P+56+68*i, while all preceding Line versions are current.
- Char count: P+56+68*L, DWORD; first Char: P+60+68*L.

These are serializer equations, not a fixed backward offset. The optional bounded
`inspect_parent_prefix` walks supplied bytes and fails closed on older/unknown
versions before using the current size. `require_parent=True` without bytes yields
`insufficient_parent_context`. Any supplied noncurrent/truncated parent vetoes
local support conservatively; this is not a claim that independently versioned
parents and children must always have matching version numbers.

The corpus's parent diagnostic solves the above length equation for bounded L,
ending at the already established first slot, and validates the version/count
sequence. It neither finds nor relocates a record and is never a predicate input.
All 84 paragraphs have one such candidate (88 Line serializers, so not all L=1).
These are **locally_derivable diagnostic parent candidates**, not new proof of
global CParagraphe framing. Whole Style's version locations are Char+0, Line at
92+E, Para at 160+E; under E=112 these are 0/204/272, so the latter two are outside
one 204-byte record. They must not be read as slot-local markers.

## Runtime corpus and variation

Every tests/samples .txt is considered by the existing content-validation inventory:
126 files, 116 valid hex captures, 10 non-hex reports. All 84 extracted paragraphs
are aligned; no paragraph is silently assigned a current result after alignment
failure. Record starts still come exclusively from existing structural candidate
alignment. Filenames are display provenance only.

| State | All | Visible | Terminal |
| --- | ---: | ---: | ---: |
| current_layout_supported | 700 | 616 | 84 |
| legacy_or_other_layout | 0 | 0 | 0 |
| unsupported_version | 0 | 0 | 0 |
| insufficient_parent_context | 0 | 0 | 0 |
| truncated | 0 | 0 | 0 |
| unresolved | 0 | 0 | 0 |

| Discriminator / context | Expected reviewed current | Observed values / count |
| --- | --- | --- |
| AttrChar record+0 | 5 | 5:700 (visible 616, terminal 84) |
| CPropertyExtend record+92 | 5 | 5:700 (visible 616, terminal 84) |
| Diagnostic parent AttrPara | 4 | 4:84 |
| Diagnostic parent AttrLine | 4 | 4:88 |
| Existing CParagraphe descriptor second word | schema candidate 6; not a predicate input | 6:84 |

No alternate extension version prefix or noncurrent local marker was observed.
Nonversion DWORDs do vary: record+8 has 0:692 and 1:8; record+44 has numerous
values, including 0:501. Their full histograms are emitted by the analyzer.
The code writes record+8 through IdSavedFont and record+44 from member+50; neither
is an additional schema/feature-version switch. No predicate was fitted to these
values or their frequencies. This adds no typed-field or flag semantics.

Variation coverage is explicitly bounded: **F4 preselects AttrChar==5**, so the
700 AttrChar matches are expected by construction, not an independent claim that
no old AttrChar exists anywhere in these captures. No new scan for arbitrary 1-4
DWORDs was introduced. All relevant existing files and extracted paragraphs were
considered; no unaligned paragraphs or conflicting diagnostic parent sequences
were observed. Anonymous bytes outside established candidates, legacy object forms,
and global MFC reference variants remain outside this alignment coverage.

There are **zero observed real nonempty extensions**. Nonempty guard mutations
are synthetic in-memory evidence only. The discriminator has not been tested on
real nonempty extension records. No synthetic captures were saved.

## F4 and empty-extension relationship

**F4 relationship = partial correlation.** F4's first token is exactly the same
AttrChar==5 condition. Its +08 and other constants do not inspect extension+0 at
record+92. Mutating only record+92 from 5 to 4 leaves the complete production
candidate unchanged, while the applicability helper rejects it. Matching 5/5
alone need not match the other F4 constants. F4 was not redefined.

The existing empty helper checks AttrChar v5 and the six zero words, but not the
extension version. An in-memory record with extension version 4 and six zero
words still satisfies that frozen helper, while the new helper rejects it.
Conversely, either positive count/length or presence=1 can preserve both versions
while making the extension nonempty. Therefore six empty conditions alone do not
establish the reviewed layout.

Future-gate evidence only:

```text
existing structural alignment
AND AttrChar version exactly 5 at record+0
AND CPropertyExtend version exactly 5 at record+92
AND bounded six_empty_conditions
=> reviewed 204-byte empty layout applicable within the reviewed serializer family
```

The helper caps its window at 204 bytes and requires a complete window for supported
evidence. It returns separate applicability and empty states. Nonempty data never
produces `combined_future_204_supported=true`; unknown or truncated input fails
closed. Both local markers precede variable framing, so neither is
`variable_framing_blocked`. Parent framing beyond the declared precondition remains
unresolved, not silently converted into support.

| Future production criterion | Evidence |
| --- | --- |
| A: serializer applicability/version structurally established | two exact local version words; scoped alignment precondition |
| B: six empty fields established | existing frozen helper |
| C: both bounded and fail closed | exact versions, bounded reads, independent combined result |
| D: terminal compatible | same serializer/helper; 84 supported |
| E: no corpus contradiction | 700 examined, no conflicting version/empty state |
| F: unsupported/legacy rejected | in-memory mutations reject lower, higher and invalid versions |

**Combined future 204-gate readiness = ready_for_production_gate_review**, under the
same existing candidate-alignment scope. There is no remaining local version-state
blocker and no `blocked_by_unserialized_version_state` outcome. Production review
still must decide how to attach these checks to the existing alignment and maintain
abstention for unaligned/unsupported inputs. This result does not authorize a
general typed parser, standalone byte scanner, global MFC schema decoder or support
for real nonempty records. No production implementation is part of this task.

## Deliverables and validation

Only four additive repository files:

- [Analyzer](../tools/analyze_text_slot_layout_applicability.py): pure shadow helper, optional parent reader and broad corpus CLI.
- [Version evidence](../tools/text_slot_layout_version_evidence.json): code-first mechanism/branch/position map.
- [Tests](../tests/integration/test_text_slot_layout_applicability.py): synthetic negatives and corpus/preservation regression.
- This report.

Run `PYTHONPATH=src python -B tools/analyze_text_slot_layout_applicability.py --json`
for all per-record evidence. The regular CLI emits the compact matrix and value
histograms. Production candidates receive no new fields.

Validation used the actual checkout's `.venv/Scripts/python.exe`, Python 3.14.7.
The requested path without a separator before `.venv` does not exist. IDE SDK
lookup returns the separately open TypeEdit_2009 Python 3.12.10, used only for
read-only vendor static inspection. No interpreter or environment was changed.

Synthetic checks cover both markers at 0/1/2/3/4/6/0x7FFFFFFF/0xFFFFFFFF,
all 204 proper-prefix truncations, oversized input, each of the six nonempty
conditions, optional/required parent input, contradictory AttrPara/AttrLine
versions, every parent proper prefix, count budgets, F4 independence, unchanged
capture renaming/reordering, and shifted enclosing-buffer offsets.

| Check | Actual result |
| --- | --- |
| New applicability tests | 36 passed |
| Existing empty-extension tests | 26 passed |
| Archive metadata tests | 16 passed |
| Historical replay assertion | 1 passed; 104 fixtures, runtime outputs equal, canonical source equal, ready_for_review |
| Combined focused invocation | 79 passed in 12.93s |
| Full actual checkout, `PYTHONPATH=src python -B -m pytest -q -p no:cacheprovider` | **1328 passed in 80.83s**, baseline 1292 + 36 |
| Ruff default, both new Python files | Passed |
| Ruff E4/E7/E9/F, both new Python files | Passed |
| `git diff --check` | Passed |
| Production source diff | Empty |
| Fixture diff | Empty |
| Existing empty-extension report, before versus after | Exact JSON equality |

Before work, a PowerShell SHA256 inventory retained every existing file under
production and tests/samples, plus the existing empty helper/model. After the full
suite, all 297 recorded raw file hashes match, with zero mismatches. Raw preservation
is a session filesystem audit, not a new Python source snapshot gate. New Python
source-integrity assertions use only `tests/source_integrity.py`'s existing
`canonical_source_sha256`. Fixtures retain exact raw bytes.

The new regression also compares the complete production dataclasses and chain
results for every valid existing hex capture before/after running the analyzer,
and checks unchanged empty-helper reports and fixture bytes. The full suite
includes the frozen F4/candidate, terminal, typed-field, archive metadata, Maximum
Length, spacing and compression regressions. Historical raw snapshot representation
differences remain informational under the existing canonical integrity policy.

No existing tracked file was edited. No production hook, gate, capture, typed
parsing, semantic relabeling, or continuation into another investigation occurred.
