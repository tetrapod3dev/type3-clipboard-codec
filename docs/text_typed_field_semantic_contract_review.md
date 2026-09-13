# Eight archive doubles: semantic naming and confidence review

Review only; no parser/schema change, alias, field, fixture or runtime investigation.
Reviewed checkout: `6db557c7b2af78790c24edab33245a3866a14636`. Supplied baseline:
1468 passed; historical104 replay has runtime/canonical equality and ready_for_review.

**Decision:** the five slot-local UI interpretations and Maximum Length remain
**Tier B: strong correlated descriptive labels only**. P+0x20 and P+0x68 have
independently confirmed model-side scale assignment/reduction roles and qualify
for **Tier A narrow internal-role naming**. This does not confirm their UI
ownership. Recommend future additive aliases for only those two roles, retaining
all eight neutral keys as canonical. No alias or rename is implemented here.

## Five independent evidence layers

* **A, archive_type_status:** existing `confirmed_archive_double`, equivalent here
  to confirmed binary64 representation; runtime f64le, width8.
* **B, structural_source_status:** `confirmed_structural_source` for the exact
  serializer/member and gated archive position. This does not establish glyph ownership.
* **C, controlled_fixture_correlation:** `strong_controlled_correlation` for the
  recorded controls. Existing `strong_style_field_candidate`,
  `spacing_ratio_f64_candidate` and `supported_crosswalk` terminology is retained.
* **D, UI/resource correspondence:** resource terminology can be confirmed while
  its association with a serialized member is only supported or unresolved.
* **E, UI_to_model_end_to_end_ownership:** `semantic_ownership_unresolved` unless
  the complete path is established. A-D do not automatically establish E.

Tier A means a **particular proposed name** is independently supported, including
a model-side algorithmic role proven without a UI callback. It does not make E
confirmed. Tier B permits correlated descriptions; Tier C only member names;
Tier D diagnostic hypotheses. These are review classifications, not new runtime enums.

The current record gate establishes AttrChar5/extension5/empty applicability.
The parent gate independently walks C to P and checks current versions, first
record alignment and counts; its three-field group requires at least one line.
These gates establish positions, not UI provenance. The line fields are always
**AttrLine[0]**, including in two-line paragraphs. Earlier Phase2 absolute-origin
limitations have been addressed by later codec structural work; missing semantic
edges have not. See the current [slot contract](text_slot_archive_double_promotion.md),
[pre-slot crosswalk](text_preslot_crosswalk_investigation.md) and
[pre-slot output contract](text_preslot_archive_double_promotion.md).

## Production contract matrix: eight rows

`S[k]` is `candidate_fields.text_slot_run.slots[i].archive_double_candidates[k]`.
`P[k]` is `candidate_fields.text_slot_run.preslot_archive_double_candidates[k]`.
**AD** means `confirmed_archive_double; f64le; width8`.
**SS** means `confirmed_structural_source` under the existing gate.
**U** means `semantic_ownership_unresolved` for end-to-end UI/model ownership.
Sources S1–T1 are linked below. `rename_safe_now` describes naming evidence, not
permission to replace an existing public key during this review.

| production_key | Record/run scope | Serializer source | Archive representation A | Structural status B | Controlled correlation C | UI correspondence D | UI-to-model ownership E | Current semantic wording | Recommended wording / tier | rename_safe_now | Remaining gap |
|---|---|---|---|---|---|---|---|---|---|---|---|
| S[`0xc`] | AttrChar, visible or terminal | Char+0x10; Style+0x18; write4D7F1 | AD | SS | Strong:10/20mm ->0.01/0.02 | Height33114/33115 resource confirmed; field link supported by controls [R1] | U | Neutral key; height-correlated / strong_style_field_candidate | `height_correlated_value`; B | No unqualified Height alias | Exact Height handler-to-member route and units not established [S1,S2] |
| S[`0x14`] | AttrChar, visible or terminal | Char+0x18; Style+0x20; write4D7FE | AD | SS | Strong:50/100/150% ->0.5/1/1.5 | Width33116/33117 resource confirmed; ratio is fixture interpretation [R1] | U | Neutral key; width-ratio candidate | `width_correlated_ratio`; B | No width_ratio alias | Exact UI/member route; no independent static semantic closure [S2] |
| S[`0x1c`] | AttrChar, visible or terminal | Char+0x20; Style+0x28; write4D80B | AD | SS | Strong:+/-15 degrees ->+/-0.2617993877991494 | Partial:33119 says Italic/character inclination; exact Slant member edge unresolved [R1,S2] | U | Neutral key; slant-correlated candidate | `slant_correlated_radian_value`; B; radians denotes fixture compatibility | No slant or slant_radians alias | Code-derived units and Slant-vs-Italic UI ownership missing |
| S[`0x40`] | AttrChar, visible or terminal | Char+0x30; Style+0x38; write4D84C | AD | SS | Strong:50/100/150% ->0.5/1/1.5 | supported_ui_correspondence:33123 Character spacing and actual callback output reference [U1] | U; supported_partial | Neutral key; spacing_ratio_f64_candidate | `character_spacing_correlated_ratio`; B | No character_spacing alias | GetValPourcent parser and SendAtribToCompo-to-model targets unresolved [U1,U4,U5] |
| S[`0x48`] | AttrChar, visible or terminal | Char+0x38; Style+0x40; write4D859 | AD | SS | Strong:+/-15 degrees ->+/-0.2617993877991494 | Rotation33120/33121 resource confirmed; member path unresolved [R1,S2] | U | Neutral key; rotation-correlated candidate | `rotation_correlated_radian_value`; B; radians denotes fixture compatibility | No rotation or rotation_radians alias | Exact UI/member route and code-derived units absent |
| P[`P+0x20`] | Run, embedded AttrPara | AttrPara+0x20 = CTxtPara+0x30; write4E253 | AD | SS | Strong layout-scalar correlation;84/84 equality with P+0x68 is diagnostic | No specific UI control assigned | U for UI; internal minimum-scale role is independently confirmed_code [M1,M2,M4] | Neutral source; compression-correlated scalar A in diagnostics | `stored_minimum_line_layout_scale`; A for internal role only | Yes, future additive internal-role alias; no replacement | Alias compatibility review; no all-state freshness/recomputation guarantee |
| P[`P+0x50`] | Run, first AttrLine | AttrLine[0]+0x30; Style+0x120; write4DE4B | AD | SS | Strong signed values:0,+0.100,+0.060,+0.040,-0.060,+0.07450,+0.07458,+0.07460,+0.07466 | supported_ui_correspondence:33141/33142 Maximum Length; GetValDist receives Style+0x120 [U2,U3] | U; supported_partial | Neutral source; signed requested maximum-length candidate | `maximum_length_correlated_signed_value`; B | No maximum_length alias | Parser/application callback edges missing; additional geometry writers mean it is not immutable UI input |
| P[`P+0x68`] | Run, first AttrLine | AttrLine[0]+0x10; write4DE72 | AD | SS | Strong layout-scalar correlation;84/84 equality with P+0x20 is diagnostic | No specific UI control assigned | U for UI; assigned-line-scale role independently confirmed_code [M1,M2] | Neutral source; compression-correlated scalar B in diagnostics | `stored_first_line_layout_scale`; A for internal role only | Yes, future additive internal-role alias; no replacement | Alias compatibility review; not an unmodified helper ratio or paragraph-wide value |

The five slot fields are all Tier B because their **individual preserved member
rows** remain supported_crosswalk, not because spacing's callback blocker was
mechanically applied to them [S2]. Their D layers differ: spacing has a concrete
control/output-reference route; height/width/rotation have resource labels without
a completed route; slant also has a terminology distinction. No field needs to
be downgraded to Tier C/D merely to populate every tier.

## UI resources and field-specific gaps

Existing Phase1 KR/US resource inventory [R1] records:

| Dialog/control | KR | US | What it proves |
|---|---|---|---|
| DlgRapido464;33114 STATIC,33115 EDIT | 문자 높이 / 높이 | Character height / Height | UI terminology, not a completed member path |
| DlgRapido464;33116 STATIC,33117 EDIT | 문자 폭 / 폭 | Character width / Width | UI terminology; percentage ratio remains controlled evidence |
| DlgRapido464;33119 EDIT | 문자 기울기 / 이탤릭 | Italic characters / Italic | Related terminology, not proven Slant model ownership |
| DlgRapido466;33120 STATIC,33121 EDIT | 문자 회전 / 회전 | Character rotation / Rotation | UI terminology, not ownership of Char+0x38 |
| DlgRapido466;33123 EDIT | 문자 간격 / 간격 | Character spacing / Space | Known partial output-reference path |
| DlgRapido467;33141 STATIC,33142 EDIT | 최대 길이 | Maximum length / Max length |33141 label/resource relation;33142 value-input control |

Templates need not embed those strings: Phase2D records33141 as SS_BITMAP.
STRINGTABLE/tooltip correspondence is not literal text in that static control [U3].

**Height:** exact Char+0x10/write4D7F1 is established.10mm/20mm ->0.01/0.02 does
not establish the handler pointer or general mm-to-m conversion. **Width:** clean
0.5/1/1.5 correlation likewise does not close a UI/member path. **Slant and
rotation:** +/-pi/12 compatibility alone does not establish a serializer-unit
contract. Existing font metric and object Rotation export names do not identify
these particular members. Phase2B explicitly retains the four full semantic
labels as correlations [S1,S2].

**Spacing:** mapped A400 tail-jumps to A200; A2F7 invokes GetValPourcent with
33123 and output Style+0x38. GetAttrib8850 repeats that control/member reference
at8C51. Model SetAttr50502 invokes Char::PartialAffectation, which copies defined
Char+0x30;4D84C serializes record+0x40. The handler's percentage/scrollbar work is
proven, but the installed edit parser and Send callback joining UI to model are
not. Keep `character_spacing_ui_to_serialization=supported_partial`.33128 is a
distinct interacting toggle, not proof of another serialized spacing property [U1].

**Maximum Length:** GetAttribB760 forms Style+0x120 atBC0C, supplies33142 atBC13,
calls GetValDist atBC20, then caches successful output at page+0x6B0 atBCA3.
Separately, model SetAttr50387 passes Style+0xF0 into Line::PartialAffectation;
4DC1E/4DC21 preserve the signed double at Line+0x30.4DE4B writes P+0x50. Two
confirmed partial routes do not prove the missing callback joining them.
Additional writers include conditional SetBaseLine4F1CA and geometry paths:
the serialized value is not guaranteed to remain the originally entered request
[U2,U3]. Thus **strong_correlated_only**, not production `maximum_length`.

Phase2E `static_registration_exhausted=true` remains a scoped search result,
not proof of absent callbacks. Phase2F stopped before DlgRapido load with
**Debugger detected (E0030)**; no bypass occurred. SendAtribToCompo, GetValDist
and GetValPourcent targets remain unresolved, not zero or proven unregistered.
This review did not launch TypeEdit, inspect new binary functions or attempt any
callback observation [U4,U5].

## 0x51E30 and the three pre-slot members

Call its operands **H_A/H_B** to avoid confusing them with the observed equal
serialized scalars. The receiver is RTTI-confirmed CTxtParaInfoLine. The frozen
finite-ordered formula is:

```text
H_A = InfoLine+0x50; H_B = InfoLine+0x68
if H_A >= H_B: return 1.0
r = H_A / H_B
return r - binary64(0.001) if r > binary64(0.001) else r
```

The literal is binary64(0.001), not rational1/1000. The x87 proof does not force
binary64 rounding after every intermediate; unordered cases are separately
documented. This is not an eligibility rule or permission to recompute fields [M1].

Confirmed copy/call/write edges relate to **all three** fields:

1. **P+0x50 initially supplies working state, not a permanent helper alias.**
   BeginCompute4EEE9 copies model Line into InfoLine+0x20, initially placing
   Line+0x30 at InfoLine+0x50. SetBaseLine4F0C7 overwrites that working member with
   CContour::Longueur's return from4F0C1 before the reviewed helper calls. H_A is
   then measured working baseline length, not simply the signed production
   value. Conditional4F1CA can later copy working state back to Line+0x30 [M1,M3].
2. **P+0x68 stores an assigned scale downstream of the helper.** Direct calls
   4F0E6/4F0F8 contribute to common-mode selection;4F16F obtains a local result.
   4F182..4F191 applies the external upper limit.4F1C2 writes the selected scale
   to model Line+0x10, then4DE72 serializes it. It need not equal one unmodified
   invocation result [M1,M2].
3. **P+0x20 stores the aggregate minimum.**4F195..4F1A0 updates the minimum across
   assigned line scales;4F1E4 writes CTxtPara+0x30, embedded AttrPara+0x20,
   subsequently serialized at4E253. The named GetCompressionHMax4CEF0 also
   reads that exact member. This writer/reduction/accessor chain independently
   supports a narrow stored-minimum-scale name [M1,M2,M4].

No production field is identified with InfoLine+0x68 merely by matching offsets
or values. That helper denominator is accumulated/reset by Compute, subsequently
mutable, and copied to model Line+8 at4EF9C (serialized at4DE65), **not** the
currently exposed request or scale members [M1,M2].

| Term | Evidence-backed distinction |
|---|---|
| Requested maximum-length value | Controlled signed setting correlated with Line+0x30; not immutable across model writers |
| Working baseline extent | InfoLine+0x50 after contour-length overwrite; not the original signed request |
| Pre-compression text extent | InfoLine+0x68 at helper entry; not an immutable natural extent or proven glyph width |
| Assigned layout scale | Helper/common-mode result after limit selection, stored in Line+0x10 |
| Minimum assigned scale | Aggregate stored in Para+0x30 / AttrPara+0x20; distinct from first-line storage |
| Serialized bbox extent | Derived CZone geometry evidence, not requested length, glyph advance or helper denominator |

The +/-60 fixture equality is compatible with the conditional two-point norm
path, not proof every captured UI action took it. Near0.999 does not establish
H_A==H_B: the helper returns1.0 at ordered equality [M1,M3].

## Equality and terminal ownership

P+0x20 and P+0x68 were raw/numerically equal in84/84 paragraphs. That is a
consistency diagnostic, not semantic proof. The independently known reduction
explains why the one-line minimum can equal its line's scale. With several lines,
the minimum need not equal the first line's value; four equal two-line examples
do not make equality universal. Keep distinct fields. Historical phrases such
as "duplicate" or `parent_line_replication` are not recommended contract names.

Slot-local values also appear on84 terminal records. Phase2C proves a zero-code
AttrChar terminal style carrier and an endpoint-inclusive SetAttr branch that
can update it. It does not establish a visible glyph, unconditional copying
from the previous visible character, or the fixture's exact UI selection dispatch.
Record field meaning and visible-character ownership remain separate [T1].

The two Tier A names describe **stored internal roles**, not guaranteed fresh
recomputation, universal equality, range validity or UI compression ownership.
They do not authorize changing raw bytes, NaN/Inf handling or numeric acceptance.
E-layer ownership remains unresolved even for these two fields.

## Explicit acceptance answers

| # | Question | Decision |
|---:|---|---|
|1|Can+0x0C be called Height?|**strong_correlated_only**; height-correlated documentation, no Height alias.|
|2|Can+0x14 be called Width ratio?|**strong_correlated_only**; width_correlated_ratio.|
|3|Can+0x1C be called Slant?|**strong_correlated_only**; no unqualified slant_radians.|
|4|Can+0x40 be called Character spacing?|**strong_correlated_only**; strong33123/reference evidence does not fill callback edges.|
|5|Can+0x48 be called Rotation?|**strong_correlated_only**; exact UI/member path remains missing.|
|6|Can P+0x20 receive a semantic name?|**yes**, stored_minimum_line_layout_scale, from confirmed model reduction/accessor, not UI ownership.|
|7|Can P+0x50 be called Maximum Length?|**strong_correlated_only**; do not rename to maximum_length.|
|8|Can P+0x68 receive a semantic name?|**yes**, stored_first_line_layout_scale, from confirmed assignment after mode/limit selection.|
|9|Which semantics are independent of callback proof?|Only those two stored scale roles among these eight; not the six UI interpretations.|
|10|Which are specifically callback-blocked?|Spacing: GetValPourcent/SendAtribToCompo. Maximum Length: GetValDist/SendAtribToCompo. The other four also lack field-specific static UI paths, so callback recovery is not their sole proven gap.|
|11|Is A/B observed equality semantically useful?|Diagnostic consistency only; the reduction relationship is established separately by code.|
|12|Does0x51E30 directly relate to any production fields?|Yes: initial copy then overwrite for P+0x50; downstream assigned scale for P+0x68; downstream minimum for P+0x20. No unqualified raw-operand alias.|
|13|Which neutral keys remain neutral?|All eight existing canonical keys; keep them even with future aliases.|
|14|Which names are documentation labels only?|The six qualified correlated UI descriptions in the matrix. Unqualified names may identify UI controls, not archive ownership.|
|15|Which future additive aliases are supported?|stored_minimum_line_layout_scale and stored_first_line_layout_scale, only for their existing gated fields.|
|16|Is any production rename justified now?|Naming support exists for those two internal roles. No key replacement/removal is recommended; no rename is implemented here.|
|17|What would overclaim?|Unqualified height/width_ratio/slant_radians/character_spacing/rotation/maximum_length; immutable UI request; universal natural glyph width; duplicate scalar; direct formula recomputation; terminal visible-glyph ownership.|
|18|Single smallest next implementation batch?|**A: additive aliases for only the two independently confirmed stored scale roles**, preserving original keys/raw values/statuses and using explicit additive compatibility checks.|

## One next batch, subject to human review

Choose **A**, limited to two additive internal-role aliases. Existing model edges
are sufficient for those names without reopening callback work. Do not combine
it with UI names, replacement keys, second-line fields or numeric validation.
The future batch must review the exact additive representation and historical
projection; schema-version migration/replacement would be a larger decision.
This review neither implements nor automatically starts that batch.

## Evidence index: existing Phase1–2F artifacts only

* **S1:** [Phase2B Style composition](C:/TypeEdit_2009/_reverse_engineering/reports/phase2b_text_attr_style_layout.md), exact members/widths and supported semantic crosswalk.
* **S2:** [Phase2B field crosswalk](C:/TypeEdit_2009/_reverse_engineering/data/phase2b_crosswalk.csv) and [summary answers28–29](C:/TypeEdit_2009/_reverse_engineering/reports/phase2b_summary.md), individual unresolved UI fields.
* **R1:** [Existing KR/US inventory](C:/TypeEdit_2009/_reverse_engineering/data/all_kr_us_resources.csv), DlgRapidoDLL STRINGTABLE33114..33123/33141/33142 and dialogs464/466/467. Read as existing CSV; no resource re-extraction.
* **U1:** [Spacing closure](C:/TypeEdit_2009/_reverse_engineering/reports/phase2c_character_spacing_closure.md) and [UI/model edges](C:/TypeEdit_2009/_reverse_engineering/data/phase2b_ui_model_edges.csv).
* **U2:** [Maximum Length closure](C:/TypeEdit_2009/_reverse_engineering/reports/phase2c_maxlength_closure.md), writers and callback limits.
* **U3:** [Dialog467 detailed audit](C:/TypeEdit_2009/_reverse_engineering/reports/phase2d_dialog467_maxlength.md), callback arguments, cache, label role and missing final mutation.
* **U4:** [Phase2E static exhaustion](C:/TypeEdit_2009/_reverse_engineering/reports/phase2e_static_exhaustion.md).
* **U5:** [Phase2F blocked startup](C:/TypeEdit_2009/_reverse_engineering/reports/phase2f_summary.md).
* **M1:** [Formula, receiver and lifecycle](C:/TypeEdit_2009/_reverse_engineering/reports/phase2b_formula_51e30.md).
* **M2:** [Member map](C:/TypeEdit_2009/_reverse_engineering/data/phase2b_member_map.csv) and preserved [SetBaseLine CFG](C:/TypeEdit_2009/_reverse_engineering/data/phase2b_cfg_MaudeTxt.dll_4f030.json),4F16F..4F1E4. Reading this existing CFG is not new decompilation.
* **M3:** [Negative-length path](C:/TypeEdit_2009/_reverse_engineering/reports/phase2c_negative_length.md) and [signed/working-state distinction](C:/TypeEdit_2009/_reverse_engineering/reports/phase2d_negative_path.md).
* **M4:** [Preserved GetCompressionHMax CFG](C:/TypeEdit_2009/_reverse_engineering/data/phase2a_cfg_MaudeTxt.dll_4cef0.json), exact CTxtPara+0x30 read; containment in M2.
* **T1:** [Terminal carrier and propagation](C:/TypeEdit_2009/_reverse_engineering/reports/phase2c_terminal_record.md).

The reference reports under `C:/TypeEdit_2009_reverse_engineering` point to these
preserved Phase1–2F files under `C:/TypeEdit_2009/_reverse_engineering`. No later
vendor reverse-engineering conclusions replace them here. Current repository
documents establish only approved runtime representation/gates and corpus scope.

## Review-only validation

Only `docs/text_typed_field_semantic_contract_review.md` is added. Production,
schema, analyzers, tests, source-integrity metadata and fixtures are unchanged.
`git diff --check` and the new document's whitespace check pass; production and
fixture diffs are empty. No helper/CSV was added, so the suite was not rerun.
1468 passed and historical104 equality are prior baseline results, not newly
executed checks. Stop here for human approval.
