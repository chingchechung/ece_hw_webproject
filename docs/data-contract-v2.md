# Assignment v2 — multiple accepted answers, one student choice

This is the instructor-approved schema/editor revision to Phase 2. It changes
teacher authoring and data validation. The original student game is **not yet
integrated with v2**; Phase 3/4 must still render actual choices and apply the
single-choice acceptance rule before v2 gameplay can be claimed.

## Public formats and compatibility

| Property | Assignment v1 | Assignment v2 |
| --- | --- | --- |
| `schemaVersion` | 1 | 2 |
| `options` per question | Exactly four nonblank strings | Three or four nonblank strings |
| Labels | A–D | A–C or A–D, in original order |
| Answer field | `correctOption: "B"` | `correctOptions: ["A", "C"]` |
| Accepted answers | One label | One or more distinct existing labels |
| Student selection | Exactly one label | Exactly one label; any accepted label passes |

The existing unit fields, optional question display fields, exact S01–S12 IDs,
Sxx.json filename match, four/five sequential questions and required HTTPS
video/form URLs remain the same as [v1](data-contract-v1.md). Unknown fields
are rejected. Never include both answer-field names in a question. V1 files
are not reinterpreted as v2 and their schema is unchanged.

The public manifest remains **schemaVersion 1** with exactly the same allowlist
entries. A current local export can be v1 or v2; each unit is validated according
to its own explicit version. Manifest export checks all allowed sources and
their associated local files. The current student prototype consumes neither
version through a loader; integration remains a separate, unapproved phase.

The formal Draft 2020-12 schema is `schemas/assignment-v2.schema.json`. The v1
schema is retained separately as `schemas/assignment-v1.schema.json`.

## V2 publish validation

- `correctOptions` is a required array with 1–4 elements. Each element must be
  exactly A, B, C or D, distinct, and correspond to an existing option position.
  D is invalid when the question has only three options. Empty arrays, duplicate
  labels, lowercase/whitespace labels, combined strings such as `"AB"`, nulls,
  non-string entries and unknown answer fields are rejected.
- `options` contains three/four nonblank strings; no empty D is added for a
  three-option question. Different questions can have different choice counts.
- There are still four/five questions with Q01–Q04/Q05 in sequence. URL rules,
  Unicode handling and ordinary-field whitespace normalization remain identical
  to v1. The Google Form URL and both URLs for each question are mandatory.
- Normalization never reorders choices or accepted labels. Accepted-label order
  has no effect on passing, but is preserved through display/save/export unless
  the instructor actually changes selections. The GUI retains original D label
  position when temporarily removing/restoring D.

Complete synthetic v2 fixtures are in `tests/fixtures/v2/S01.json` (four
questions), `S02.json` (five), and their v1-format test manifest. They contain
dummy text and demonstration URLs only. They are separate from the instructor's
incomplete course reference and must never be uploaded.

## Single-choice rule and API

For a validated v2 question, the student submits one label. The acceptance rule
is membership in `correctOptions`; it is not set equality or “select all.”
For example, accepted `["A", "C"]` means either A **or** C passes, while B fails.
An array of student selections is invalid. There is no partial credit or score.

Python APIs in `tools/assignment_data.py`:

- `validate_unit(data, filename=None)` dispatches by explicit schema version.
- `validate_unit_v1(...)` and `validate_unit_v2(...)` enforce the named version
  and reject the other version. Neither performs migration.
- `normalize_unit(...)` remains a non-mutating ordinary-field normalizer.
- `accepts_answer(question, selected)` is a pure single-label helper supporting
  the two field formats. It rejects malformed acceptance lists, mixed answer
  fields, absent positions and multi-selections. It has no maze/session effects.

The corresponding browser APIs remain in `AssignmentValidator`:
`validateUnit`, `validateUnitV1`, `validateUnitV2`, `normalizeUnit`, and
`acceptsAnswer`. Load `assignment-rules.js` before `assignment-validator.js` as
before. Error arrays continue to contain precise `path`, `code`, `message`
entries, including accepted-label indexes such as
`$.questions[2].correctOptions[1]`. The validator/helper is not wired into the
student page and does not fetch or display units.

The read-only CLI supports both versions and unchanged manifests:

```sh
python tools/validate_assignments.py tests/fixtures/S01.json
python tools/validate_assignments.py tests/fixtures/v2/S01.json
python tools/validate_assignments.py tests/fixtures/v2/manifest.json
```

All publish/export gates use these validators. No parallel exporter-specific
answer rules or schema auto-conversion are used.

## Private drafts and explicit migration

New GUI sessions create v2 drafts. For programmatic backward compatibility,
`UnitDraft.new` and `EditorModel` retain their v1 defaults; pass
`schema_version=2` for v2. Existing v1 drafts continue to save in their original
four-key private envelope, with `draftVersion: 1`, `allowPlay`, `unit`, and
`parkedQuestion`. Legacy GUI mode retains its one-answer radio group.

V2 private envelopes use exactly these five keys:

| Field | Meaning |
| --- | --- |
| `draftVersion` | Integer 2 |
| `allowPlay` | Private boolean; never part of public unit JSON |
| `unit` | Editable assignment with `schemaVersion: 2` |
| `parkedQuestion` | Null or temporarily removed Q05 |
| `parkedOptions` | Map from question ID to retained D metadata |

Each retained D record has `text` (string), `accepted` (boolean) and `position`
(original accepted-label index 0–3, or null when unaccepted). Records may refer
to an active or retained Q05, but that question must have three active options.
Unknown fields, mismatched versions and malformed retained state are rejected
on import. Private metadata is never exported to unit JSON or the manifest.

Incomplete private v2 drafts can have `correctOptions: []` and blank required
URLs. Saving is allowed; public export is blocked. Removing D also removes it
from active accepted labels. If D was the only answer, the active answer list
becomes empty until the instructor checks another label or restores D. This
prevents an invisible D from counting as a publishable answer.

**Convert v1 to v2** is explicit and confirmed. It creates an unsaved copy,
wraps each existing v1 answer in a one-item list, converts a blank draft answer
to `[]`, and converts retained Q05 too. It does not modify the original object
or file. Invalid v1 answer strings must be fixed first. Save to a new filename
to retain both versions; an explicit overwrite still requires normal consent.
No automatic or lossy v2-to-v1 conversion is implemented.

The Allow Play flag survives deliberate conversion, but the previous v1 unit
export becomes stale relative to v2 source data. Manifest export stays blocked
until the current version is explicitly exported to the selected local folder.
All prior atomic-save, overwrite, conflict, private-directory and unsaved-change
protections remain in effect.

## Instructor S01 reference

`S01_reference_v2_incomplete.json` is initial private authoring content, not a
publishable fixture. It has five questions and a three-option Q05. Preserve
all source text, original choice order and accepted labels, including Chinese
choices in Q04. No translation or factual rewrite is authorized. The supplied
Q03 absolute wording remains for instructor confirmation; it was not corrected.

The form URL and ten video URLs are intentionally empty. The reference therefore
has **11 missing-link errors** and cannot be publicly exported. Do not substitute
example or fabricated URLs to make it pass. The initial draft was prepared in
ignored `teacher_data/S01.draft.json`, with Allow Play off. It is not included
in Git or `assignments/`.

Use **Import Reference** for the original filename, or launch explicitly:

```powershell
py -3.12 tools\assignment_editor.py --reference "C:\path\to\S01_reference_v2_incomplete.json"
```

Use `--draft <private-file>` to reopen a saved draft. Normal Load / Import still
enforces Sxx.json names for public-unit imports; only the explicit authoring
reference action accepts other filenames. All final unit exports still use
the exact Sxx.json name and full publish validation.

Neither these operations nor Allow Play performs an upload. Instructor workflow
remains local drafts → validated local units → validated manifest → manual upload
of units first, manifest last. Public answers remain visible in static JSON;
no backend, grading, submission tracking or form availability logic was added.
