# Phase 2 revision — v2 multiple accepted answers

Implemented on 2026-10-20 from the requested `Codex_multianswer_v2.md` changes,
using the supplied incomplete S01 as private authoring data. This revision
stops at schema/editor work. **Phase 3 has not started and the student game has
not gained v2 gameplay support.**

## Result

- Separate v2 JSON Schema, three/four options per question, distinct nonempty
  accepted labels matching actual option positions. Python and browser validators
  dispatch by version and also expose strict v1/v2 APIs. CLI validates both.
- Original v1 schema and public/private v1 formats retained. Existing v1 GUI
  workflows remain covered by the original eight smoke tests. Conversion creates
  an explicitly confirmed, unsaved v2 copy; no silent migration or source rewrite.
- New v2 teacher drafts use independent checkboxes, with each question selecting
  three/four options independently. Temporary D removal retains text, acceptance
  and accepted-label position privately, including when Q05 is also retained.
- Public manifest stays v1. All completed Phase 2 features remain: S01–S12,
  incomplete drafts, separate Allow Play, save/load/batch reopen, precise errors,
  validated local exports, freshness checks, atomic writes, overwrite/conflict
  handling and unsaved-change prompts. No upload or deployment functionality.
- Explicit Import Reference and `--reference` support authoring filenames;
  `--draft` opens saved authoring data. Final export filename checks remain strict.
- Pure single-choice answer helpers are tested in Python/Node/Chromium: any one
  accepted label passes, and multi-selections/invalid labels fail. These helpers
  are **not** connected to maze controls or wrong-answer/finish state yet.

## Private S01 preparation and verification

Prepared `teacher_data/S01.draft.json`, excluded by `.gitignore`. Compared the
saved/reloaded unit directly with the uploaded reference: exact equality, five
questions, 4/4/4/4/3 options, original accepted labels, unchanged Chinese text,
and Allow Play off. Form and video URLs remain empty. Validation reports exactly
11 blank required links and blocks public export. No course answers/reference
content were added to Git or public `assignments/`.

An additional real Tk window loaded this actual private draft, rendered five
question tabs with 4/4/4/4/3 answer widgets and flushed back to model state. Its
unit still matched the original uploaded JSON exactly; all 11 URL errors and
unchecked Allow Play remained. No translation, invented fourth choice or fake
link was inserted. Q03 wording remains for instructor confirmation as requested.

The private draft does not travel with a Git clone. On the instructor's Windows
machine, use Import Reference or `--reference` on the JSON extracted from the
supplied ZIP, then save it to a private `.draft.json` file.

## Actual test results

Linux, Python 3.12.14, Tcl/Tk 9.0.4; real Tk via the existing rootless Xvfb at
`:97` (1440×1000, no TCP listener). Test setup is temporary and not a dependency
of the application. Native file/message dialogs are mocked in repeatable GUI
tests; widgets and mainloops actually run.

| Command/check | Result |
| --- | --- |
| `python -m unittest discover -s tests -v` | **46 passed**, including all previous 31 checks and 15 new v2 checks |
| `DISPLAY=:97 python tests/gui_smoke.py` | **16 passed**: eight original v1 tests and eight new v2 tests |
| `python tests/browser_baseline.py` | **4 passed**, 800 original mazes across all sizes, both views and original reset/map/link behavior |
| `python tests/browser_validation.py` | **1 passed**; 364 contract cases, 76 single-choice cases, strict v1/v2 API checks |
| `python tools/validate_assignments.py tests/fixtures/manifest.json tests/fixtures/v2/manifest.json assignments/manifest.json` | All valid, exit 0 |
| `python -m compileall -q tools tests` | Passed |
| `node --check js/assignment-validator.js` | Passed |

The 364 shared cases retain all 296 original cases plus 68 v2 cases. They check
Python/Node error and normalization parity and formal JSON Schema agreement.
They include one/two/three/four accepted labels, mixed 3/4 choice counts, empty
lists, duplicate/invalid/out-of-range labels, type errors, wrong versions,
mixed answer fields, filenames, missing URLs and Unicode preservation.

New model tests cover all twelve incomplete v2 drafts, empty acceptance,
retained D plus Q05 save/reopen, source-preserving v1 conversion, private version
and metadata rejection, missing links, explicit reference import, mixed-version
manifest export, answer/count/version staleness, failed atomic save, external
conflicts and numeric schema-version round trips. Single-choice helpers reject
answer arrays; this tests domain semantics rather than claiming migrated gameplay.

New GUI tests exercise real checkboxes, independent selections, actual choice
count combobox events, retained D, v1 conversion confirmation, reference import,
incomplete saves, manifest staleness and unit switching. A separate interpreter
runs the real entry point with both `--reference` and `--draft`, verifies the
instantiated source/model/widgets and briefly runs the Tk mainloop. Synthetic
screenshots are at ignored `test-results/editor-v2.png` and were visually checked.
No callback errors occurred. No real YouTube or Google Forms requests were made.

## Changed files

- `AGENTS.md`, `Plan.md`: approved v2 supplement, preserving v1 rules and the
  stop-before-Phase-3 boundary.
- `schemas/assignment-v2.schema.json`: separate formal v2 schema.
- `tools/assignment_data.py`: versioned validation and pure single-choice helper.
- `js/assignment-validator.js`: matching browser APIs and answer helper.
- `tools/validate_assignments.py`: v1/v2 CLI description; existing validation
  entry point now dispatches through the shared versioned validator.
- `tools/assignment_editor_model.py`: v2 draft state, retained D, explicit
  migration, version-safe import/export and reference import.
- `tools/assignment_editor.py`: checkbox/option-count forms, explicit conversion,
  reference action/CLI and preserved legacy mode/workflows.
- `tests/contract_cases.py`, `tests/contract_cases_v2.py`: shared acceptance and
  single-choice cases using synthetic content only.
- `tests/test_assignment_data.py`: formal schema agreement by explicit version.
- `tests/test_assignment_v2.py`: strict validation, helper, model, migration and
  export regressions.
- `tests/browser_validation.py`: both versions, strict APIs and answer semantics.
- `tests/gui_smoke.py`: original v1 coverage plus real v2 widget/startup coverage.
- `tests/fixtures/v2/S01.json`, `tests/fixtures/v2/S02.json`,
  `tests/fixtures/v2/manifest.json`: complete synthetic test-only examples.
- `README.md`, `docs/assignment-editor-guide.md`: launch/import, v1/v2 workflows,
  private reference handling and manual checks.
- `docs/data-contract-v2.md`: public/private versioned contract and APIs.
- `docs/phase-2-multianswer-results.md`: this report.

Unchanged: original ZIP and extracted game, v1 schema, manifest schema, public
manifest/assignments and original v1 fixtures. Private S01 and screenshots are
excluded from the commit.

## Windows 11 review and limits

Install Python 3.12 with Tcl/Tk, then run `py -3.12 tools\assignment_editor.py`.
Follow the guide's desktop checklist, especially these new cases:

1. Import the supplied reference explicitly; verify Q04 remains Chinese, Q05
   has three choices, all accepted flags match your source and URLs stay blank.
2. Select one/two/three accepted checkboxes independently. Save/reopen, including
   zero checked labels: drafts may save, while public export must reject zero.
3. Mark D, switch to three options, save/reopen and restore four. Check text and
   acceptance, including while the fifth question has been temporarily removed.
4. Decline conversion of a v1 draft, then convert a copy and save under a new
   name. Verify the original file and retained Q05 remain intact.
5. Export allowed complete units, change accepted flags/counts, and confirm stale
   manifest export is blocked. Test native overwrite/cancel/conflict dialogs.

Windows/macOS GUI, native modal dialogs, DPI, fonts/Unicode rendering, accessibility
and native filesystem operations remain untested on those actual platforms.
Linux Xvfb/Chromium results do not establish cross-platform compatibility.
Validation checks local syntax/structure, not video language, truth of course
content, live links or form availability. Existing local-filesystem/concurrency
and unsaved-memory limitations from Phase 2 still apply. No autosave was added.

The browser game still has its original four fixed demo questions, answer field
and UI. Actual three/four-choice v2 gameplay, dynamic loading, membership-based
passing, reset integration and unit selection remain Phase 3/4 work. **Stop here
for instructor review before Phase 3.** Delivery branch is the existing `work`.
