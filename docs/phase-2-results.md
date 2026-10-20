# Phase 2 — Offline Python assignment editor

Implemented on 2026-10-20 after approval of Phases 0–1, on the existing `work`
branch. Scope stops at Phase 2; student JSON loading and visual changes have
not started. The original v1.2 files, public manifest, fixtures, schemas,
Phase 1 validators, `AGENTS.md` and `Plan.md` remain unchanged.

## Delivered behavior

- Executable Python 3.12 standard-library Tkinter/ttk application, with no pip
  dependency or network operation. Launch `python tools/assignment_editor.py`.
- S01–S12 list with titles, completeness/error count, dirty/saved state, Allow
  Play state and current/stale/missing local export status. Selected unit has
  a native Allow Play checkbox; all settings remain local until explicit export.
- Unit title/form URL, four/five question tabs, scrollable fields, optional
  display text, both required video links, A–D options and a single radio answer.
  Q05 is retained privately when switching to four and restored when switching
  back to five, including after draft save/reload.
- Independent incomplete private drafts, individual load/import, batch reopening
  of standard Sxx.draft.json files, save/save-as, new selected unit and precise
  validation messages. Switching keeps unsaved memory edits when requested.
  Replacement/close prompts distinguish save, keep/discard and cancel.
- Public unit exports reuse `normalize_unit` and `validate_unit`; no alternate
  publish validator or public schema changes. Draft saves preserve authored
  whitespace, Unicode, option order, Allow Play and retained Q05.
- Manifest export includes only explicitly allowed units, validates every source,
  rereads/validates each associated local export and compares normalized public
  content. Missing, stale, malformed or symlinked files block the write. An
  empty manifest needs confirmation in the GUI. Disabling a unit deletes no files.
- Safe local writes: UTF-8, readable JSON, same-directory temporary files,
  flush/fsync, atomic replacement, no-clobber first creation, visible errors,
  temporary cleanup and saved-state updates only after success. Loaded draft
  digests protect against accidental overwrite of external changes/deletion.
- Private/public directory guards, explicit overwrite/cancel dialogs, no auto
  copy into `assignments/`, and manual upload-order instructions after exports.

## Verification actually performed

Environment: Python 3.12.14, Tcl/Tk 9.0.4, Linux; Xvfb 21.1.16 unpacked into
`/tmp/emi-maze-xvfb` because system package installation was not permitted.
The X server used `:96 -screen 0 1440x1000x24 -nolisten tcp -ac` for local tests.
This test setup is not an application dependency and is not in Git.

| Command | Actual result |
| --- | --- |
| `python -m unittest discover -s tests -v` | **31 passed**, no skips here |
| `DISPLAY=:96 python tests/gui_smoke.py` | **8 passed**, real Tk widgets/display |
| `python tests/browser_baseline.py` | **4 passed**, including 800 generated mazes over all original sizes |
| `python tests/browser_validation.py` | **1 passed**, all 296 contract cases agree with Python in Chromium |
| `python -S tools/assignment_editor.py --help` | Passed without site packages |
| `python -S tools/validate_assignments.py tests/fixtures/manifest.json assignments/manifest.json` | Both valid, exit 0 |
| `python -m compileall -q tools tests` | Passed |

The 31 discovery tests include the previous 12 checks and 19 new model/file
tests. New coverage includes all twelve independent incomplete drafts, Unicode
and multiline round trips, four/five/retained-Q05 behavior, valid/invalid exports,
shortened form-link syntax, Allow Play gating, empty manifests, missing
and stale exports, external tampering, import safety, filename/schema agreement,
source-directory privacy, symlink aliases, private/export mixing, explicit
overwrite, concurrent first-file creation, failed replace/fsync cleanup and
deterministic UTF-8 output.

Eight GUI smoke tests instantiate actual Tk windows. They exercise real text
widgets, entries, tree selection events, question tabs, radio/check buttons,
actions, wheel scrolling and focus visibility. They drive load/save/export,
field-level errors, canceled operations, save conflicts, all-unit reopen, close
save-all/cancel and manifest staleness. Native file/message dialogs are replaced
by deterministic test answers; actual native modal dialogs remain manual checks.
No callback errors occurred. A screenshot was captured and visually inspected
at `test-results/phase-2-editor.png` (ignored, synthetic data only).

No real assignment draft or teacher export was created in the repository.
Generated test files use temporary directories and are removed after tests.
The tests use dummy fixture content and never contact YouTube or Google Forms.

## Exact changed files

- `tools/assignment_editor.py` — complete Tkinter/ttk entry point, forms, controls,
  selection/prompts, error display and local workflow.
- `tools/assignment_editor_model.py` — display-independent draft state/import,
  retained Q05, freshness checks, validated export and atomic local writes.
- `tests/test_assignment_editor_model.py` — 19 new headless business/file tests.
- `tests/gui_smoke.py` — eight real-display widget/controller smoke tests.
- `README.md` — Windows 11 Python/Tk installation and launch, folder/export
  workflow, test commands and Phase 2 status.
- `docs/assignment-editor-guide.md` — detailed private format, controls, saves,
  validation/export/manual upload and desktop verification checklist.
- `docs/phase-2-results.md` — this implementation/verification report.

## Limits and remaining manual checks

- Actual Windows 11 and macOS desktop GUI, native dialogs, DPI/scaling, system
  fonts/Unicode rendering, assistive technology and native filesystem behavior
  remain **untested**. Linux Xvfb results do not establish cross-platform support.
  Cloud Tk/X11 uses a minimal font environment; Unicode data round trips passed,
  while desktop font rendering must be checked on the instructor's machine.
- Follow the editor guide's manual checklist on Windows 11: edit an incomplete
  unit, save/reopen, switch with each prompt choice, restore retained Q05, use
  the A–D radios, test Unicode, export four/five-question units, invalidate an
  export, regenerate the allowlist and verify overwrite/cancel/native dialogs.
- Filesystem conflict detection does not provide multi-process locking or full
  power-loss durability. Unsupported filesystem operations fail visibly. No
  autosave or backup is promised; save drafts frequently and keep private backups.
- The editor blocks known source/public directories and obvious network paths,
  but cannot identify every custom web/sync folder selected by the instructor.
  Only manually chosen local exports should be uploaded. Save drafts separately.
- Validation is offline syntax/structure checking, not live URL/language/content
  verification. Submission acceptance remains entirely in Google Forms.
- Exporting does not save the draft. Public freshness compares normalized active
  content, so trimmed-only whitespace/local metadata/retained inactive Q05 do
  not make an otherwise identical unit export stale. Manifest export always
  rereads files; the status list is not a continuous filesystem watcher.
- The original student prototype still uses its original fixed questions. It
  does not consume these exports or the manifest yet. No upload, backend, student
  tracking, rendering change or Phase 3 work was added.

Phase 2 implementation prerequisites for Phase 3 are satisfied. **Phase 3 remains
blocked on instructor review and approval of the actual GUI workflow.**
Delivery branch: `chingchechung/ece_hw_webproject:work`. See Git history for the
committed source/tests/docs revision.
