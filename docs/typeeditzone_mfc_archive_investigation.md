# TypeEditZone MFC CArchive Compatibility Investigation

Status: first analyzer-only compatibility audit complete; parser refactor not ready.

[Color Phase 1](text_color_decode_rfc.md) proceeded using descriptor/payload provenance without a parser refactor.
This track is independent of anchor and color ownership. The anchor closeout is
unchanged: semantic ownership unresolved, implementation deferred,
`matched_chain=None`, active anchors and `baseline_midpoint` unchanged.

## Reference basis and tested hypothesis

Microsoft TN002 describes `WriteObject` using null (0), new-class (FFFF), and
old-class (8000 high-bit family) tags. Classes and objects share sequential
archive-local PIDs starting at 1. Large references use a 7FFF prefix and a wider
value. These identifiers are not application object IDs. The class description
contains schema and ASCII class name; class-specific `Serialize` data follows.
[Microsoft TN002](https://learn.microsoft.com/en-us/cpp/mfc/tn002-persistent-object-data-format?view=msvc-170).

The exact little-endian WORD layout below is the supplied
`CRuntimeClass::Store` implementation fingerprint, tested independently as a
compatibility hypothesis. TN002's conceptual description alone is not a
guarantee that every MFC version or serialization entry point uses this layout.

```text
FFFF : WORD schema : WORD ASCII-name-length : exact ASCII name bytes
```

MFC also permits direct `Serialize` calls without `WriteObject` overhead, and
explicit `SerializeClass` calls. Custom application framing or a mixture of
primitive writes and object serialization therefore remains possible. Failure to
follow a complete WriteObject stream is not evidence against every use of MFC.
[TN002: Calling Serialize Directly](https://learn.microsoft.com/en-us/cpp/mfc/tn002-persistent-object-data-format?view=msvc-170#calling-serialize-directly),
[CArchive::SerializeClass](https://learn.microsoft.com/en-us/cpp/mfc/reference/carchive-class?view=msvc-170#serializeclass).

## Analyzer and bounded execution

`tools/analyze_typeeditzone_mfc_archive.py` is a new, standalone analyzer. It does
not extend existing analyzers or change parser/decoder/model code. No new fixture
capture or ownership/color investigation is performed.

```powershell
$env:PYTHONPATH = 'src'
.venv/Scripts/python.exe tools/analyze_typeeditzone_mfc_archive.py
.venv/Scripts/python.exe tools/analyze_typeeditzone_mfc_archive.py --json
.venv/Scripts/python.exe tools/analyze_typeeditzone_mfc_archive.py --markdown
.venv/Scripts/python.exe tools/analyze_typeeditzone_mfc_archive.py --fixture default_text.txt --fixture default_rectangle.txt
```

- Phase A finds the six fixed known ASCII names directly in raw decoded bytes,
  without calling the class scanner. It checks preceding 2/4/6/8 bytes and each
  exact tag/schema/length/name layout, and serializes the evidence before Phase E.
- Phase B aggregates observed lengths, exact descriptor matches, and per-class
  schemas. A schema is a broad WORD candidate, provisionally excluding FFFF;
  plausibility alone is weak evidence. Schema summaries use exact descriptors,
  not arbitrary preceding words near every ASCII hit.
- Phase C inventories exact descriptor tags and probes only payload byte zero
  and the end of the first descriptor. No whole-payload tag histogram or search
  for matching PID values is used. Tag-like words at unverified cursors are
  unresolved, even when their high bit resembles an old-class reference.
- Phase D evaluates two preselected start hypotheses: payload zero, and the
  first exact descriptor if different. Each assumes a fresh WriteObject context
  without pre-mapped objects. The second is an independently declared local
  hypothesis, not recovery from the first path's failure. Both stop at the first
  unknown extent/reference; no forward resynchronization occurs.
- Phase E calls the unchanged scanner with the active parser's existing
  top-level-origin logic, then normalizes its locations to clipboard byte zero.
  It compares positions with frozen raw hits, not the other way around.

Defaults and hard inventory ceilings are 8 fixtures and 100 class hits per
fixture. `--max-fixtures` and `--max-class-hits` can reduce those ceilings.
`--context-bytes` defaults to 16 on each side and accepts 0..64. Inputs are limited
to 1 MiB decoded / 8 MiB hex text, and tag detail to 100 rows globally. Missing
fixtures produce warnings. Bounded counts are explicitly lower bounds when
inventory limits are reached. Output-budget trimming preserves summaries and
reports omitted context/hit detail. There are no full payload dumps.

All offsets use decoded clipboard payload byte zero and have
`absolute_offset_role="diagnostic_only"`. None is a parser rule or an object ID.
Fixture names select files and label reports; they do not select interpretations.

## Default corpus results

Eight existing fixtures cover three text and five geometry cases:

| Fixture | Category | ASCII hits | Exact descriptors |
| --- | --- | ---: | ---: |
| text/default_text.txt | Text | 10 | 5 |
| text/text_group_same_color_two_objects.txt | Text | 14 | 5 |
| text/text_three_objects_grouped_order_abc.txt | Text | 18 | 5 |
| default_rectangle.txt | Geometry | 7 | 4 |
| default_circle.txt | Geometry | 7 | 4 |
| polyline_5_points.txt | Geometry | 7 | 4 |
| two_rectangle.txt | Geometry | 10 | 4 |
| two_circle.txt | Geometry | 10 | 4 |
| **Total** | | **83** | **35** |

### Exact descriptors, lengths, and schemas

| Class | ASCII length | Hits | Exact matches | Observed schema in exact descriptors | Length match rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| CZone | 5 | 8 | 8 | 1 | 100% |
| CParagraphe | 11 | 3 | 3 | 6 | 100% |
| CCourbe | 7 | 8 | 8 | 1 | 100% |
| CContour | 8 | 8 | 8 | 2 | 100% |
| CPropertyExtend | 15 | 8 | 8 | 5 | 100% |
| CObDao | 6 | 48 | 0 | Not established | 0% |

Exact observed prefixes before the ASCII names:

```text
CZone            ff ff 01 00 05 00
CParagraphe      ff ff 06 00 0b 00
CCourbe          ff ff 01 00 07 00
CContour         ff ff 02 00 08 00
CPropertyExtend  ff ff 05 00 0f 00
```

All 35 matches include `wNewClassTag`-compatible FFFF bytes, exact WORD lengths,
and stable schema candidates across fixtures. Schemas are stable **per class**,
but not unique identifiers: CZone and CCourbe both use 1. The shared classes have
the same pattern and schemas in text and geometry; this is not text-only evidence.

CObDao has preceding bytes `06 00 00 00`. At the tested WORD positions that gives
schema-candidate 6 and name-length-candidate 0, so it fails the descriptor and
length-only checks. The four bytes resemble a DWORD length 6; this is a custom
string-layout observation, not a decoded MFC runtime class. Nearby
OBJETINFOS_CLASSNAME strings are context, not part of the six-name descriptor
inventory and not interpreted as object boundaries.

There are zero untagged Store-like matches and zero length-only matches in this
default corpus. The analyzer and synthetic tests still distinguish both weaker
layouts. `CParagraphe` is 11 ASCII bytes: the positive synthetic length is 0B,
and 0A must fail regardless of a preceding FFFF.

### Tags, references, repeated classes, and contexts

The bounded tag probes yield 35 exact new-class candidates plus 16 unresolved
words: 8 old-class-looking words at the first opaque body start, 5 null-looking
words at geometry payload zero, and 3 object-reference-looking words at text
payload zero. None of those 16 is confirmed framing. No extended tag is found
at these tested positions; no statement is made about every word in the payload.

In particular, an 8000-family value in data currently read as bbox bytes is not
a validated class reference. There is no synchronized cursor or established
class PID for it. Confirmed old-class, object-reference, null, and extended tag
counts are all zero. The analyzer does not claim those tags cannot occur elsewhere.

The five descriptor classes occur once per applicable fixture, including the
two-object geometry samples. The repeated ASCII name is CObDao (5/9/13 times in
the three text fixtures, 3/3/3/6/6 in geometry), and it is not an exact descriptor.
This neither demonstrates old-class substitution for subsequent objects nor
establishes context restart. There is no independently observed restart boundary
or PID reset. Repeated names alone cannot establish multiple archives.

All 16 shadow paths desynchronize:

- Under the payload-zero assumption, text stops immediately at an unresolved
  value 1. Geometry conditionally consumes two null-looking words, then stops
  at an unresolved 1 or 2. This does not decode the application prefix as MFC.
- Under the first-descriptor assumption, one CZone description is compatible
  with candidate class PID 1, object PID 2, and next PID 3. The path stops at the
  unknown Serialize extent, before assigning later PIDs. A class-only call would
  instead leave candidate next PID 2; the observed descriptor cannot choose
  between those entry points.

The local starts are observed at byte 70 in these text fixtures and byte 6 in
these geometry fixtures. Those positions are diagnostic results of name matching,
not constants used to start a parser. Seeded paths stop at bytes 81 and 17,
respectively. No coherent whole-context PID progression has been established.
One archive, several archives, and mixed application/archive framing remain
unresolved; unsupported synchronization is not labeled a format contradiction.

## Scanner relationship and architectural implication

All 35 scanner node starts equal the exact descriptor starts, six bytes before
the ASCII names. None equals the ASCII name start. The observed relation is
**A: descriptor start**, not a demonstrated TYPE3 object-block boundary.

This is not another independent fingerprint: the current scanner already checks
FFFF, the length WORD, and plausible printable class text. It slices payloads at
the next plausible header and has no archive PID/context state. Its success is
compatible with finding runtime-class descriptions while missing reference-only
framing, but the existence and extent of those missing records are not proven.

The alternative architectural hypothesis is:

```text
archive framing -> runtime-class descriptors / class tags -> TYPE3 Serialize data
```

This may ultimately explain more than `class header scanner -> class payload`,
but it first needs an independently justified Serialize extent and coherent
reference/state evidence. It is not grounds to replace the scanner, reinterpret
archive PIDs as semantic TYPE3 object IDs, or infer ownership. No refactor is
performed and `parser_refactor_readiness` remains `not_ready`.

## Assessment and next action

Per fixture: `partial_mfc_runtimeclass_framing_match` (all eight).

Global: `mfc_runtimeclass_framing_supported_but_writeobject_unclear`.

Multiple classes, exact lengths/tags, stable per-class schemas, and cross-category
agreement support compatibility with the supplied runtime-class framing pattern.
The length check is part of the exact layout test, not an independent second
vote, and scanner agreement is not an independent vote either. Coherent
old-class references, PID progression, and whole-context consistency are missing,
so the audit does not promote to strong WriteObject framing or source-code
certainty. Custom/MFC-inspired serialization remains possible.

Color candidate investigation can proceed unchanged under the existing cautious
policy. An MFC framing RFC and new independent evidence should precede any
archive-based parser redesign or structural ownership rule. This compatibility
audit neither solves ownership nor reopens the anchor implementation track.

## Verification

Default output: text 1,767 bytes, Markdown 1,853 bytes, compact JSON 99,859 bytes
including Windows newlines; all 83 hit rows and 35 scanner rows retained, with
no default truncation warning. JSON stays below 100 KB; text stays below 50 KB.

The integration tests cover CLI formats, bounds, representative coverage, exact
bytes and schema values, missing fixtures, determinism, raw/scanner independence,
and parser/decoder/model source bytes plus active parser objects before/after.
Synthetic unit tests cover correct and incorrect lengths, multiple schemas,
missing tag, length-only strings, coincidental FFFF, old/extended-looking words
without state, schema sentinel, repeated names without restart proof, and strict
stop-before-later-descriptor behavior.

Mandatory commands (using the repository virtual environment):

```powershell
$env:PYTHONPATH = 'src'
.venv/Scripts/python.exe -m pytest tests/integration/test_typeeditzone_mfc_archive_analysis_cli.py -q
.venv/Scripts/python.exe -m pytest -q
```

Integration: 8 passed. Synthetic unit tests: 15 passed. Full suite: 334 passed
(previous baseline 311). No parser, decoder, model, scanner, or anchor closeout
source/document changes are part of this audit.
