# Offline assignment editor

Run `python tools/assignment_editor.py` from the repository root, or on Windows
`py -3.12 tools\assignment_editor.py`. Python 3.12 with standard-library
Tkinter/ttk is sufficient. Keep the complete `tools/` and `schemas/` directories
together. There are no pip dependencies, remote connections, accounts, upload
credentials or server settings in the application.

New authoring sessions create v2 drafts. The [v2 contract](data-contract-v2.md)
supports three/four options with one or more teacher-accepted labels. Existing
v1 files stay v1 until explicitly converted. This changes the editor only: the
student maze still uses its original demo questions and has not gained v2 support.

## Private folders and first launch

Start with an empty in-memory set of S01–S12. Nothing is loaded, saved or exported
automatically. Suggested private locations are:

```text
<home>/EMI Maze Quest/teacher_data/S01.draft.json
<home>/EMI Maze Quest/teacher_data/...
<home>/EMI Maze Quest/export/assignments/S01.json
<home>/EMI Maze Quest/export/assignments/manifest.json
```

Create/select folders in the native file picker. When the suggested folder does
not exist, the picker starts in your home directory. All destinations are local
files chosen by the instructor. Keep drafts outside every served web directory.
The repository's ignored `teacher_data/` and `export/` directories are optional
local alternatives, provided the repository itself is never served publicly.

The editor rejects writes into checked-in/public repository directories, including
`assignments/`, the original student prototype, aliases into those directories,
and symlink targets. Export is blocked if that folder contains `.draft.json`
files. In the GUI, the export folder cannot contain the current private draft
folder, and drafts cannot be saved inside the chosen export folder. The app
cannot identify every external Apache/document root or cloud-backed OS folder;
choose private, local folders rather than a web/sync directory.

## Editing and Allow Play

Select S01–S12 in the left list. The right-hand editor contains unit title,
Google Form URL, question count and the selected unit's **Allow Play (local
only)** checkbox. The list shows each unit's title, completeness, saved/unsaved
status, Allow Play state and export status. Double-click the Allow column to
toggle that unit; the selected unit's checkbox is the main control.

Each question has a notebook tab and scrollable form: optional title and prompt,
required English question/explanation YouTube URLs, options in their original
order and optional explanation text. In v2, select three or four options per
question and independently check every accepted label. A single-correct question
uses one checked box. Students will choose just one label; any checked label
will pass once gameplay integration is approved. Empty acceptance is savable
privately but blocks public export. Legacy v1 editing keeps its original four
options and one-answer radio group.
The explanation URL is required for export although viewing remains optional.

Use the count selector to add Q05. Changing back to four questions retains Q05
privately, including its options/answer, and switching to five restores it.
Saved private drafts preserve this retained question. Four-question public
exports contain only Q01–Q04; no retained question or local metadata is exported.
Changing a v2 question from four options to three similarly retains D's text,
accepted flag and original answer-list position privately. D is removed from
active `correctOptions`; switching back restores it. Retained D can survive
alongside a retained Q05 and survives save/reopen. An originally three-option
reference is loaded with exactly three options; no fourth option is invented.

Tab/Shift+Tab navigate fields, arrow keys work in the native radio group, and
focused controls scroll into view. Use the mouse wheel or scrollbar for long
forms. Text boxes support multiple lines; URL/option fields are single-line
entries. Ctrl+S saves the selected draft; Ctrl+Shift+S opens Save Draft As.

## Save, load, switch and close

- **Save Draft** writes the selected unit, whether complete or incomplete.
  The first save asks for a `.draft.json` path. Ordinary saves to the same loaded
  file detect external changes before replacement. **Save Draft As** selects a
  different file and confirms replacement when it already exists.
- **Load / Import** opens one private draft or a public `Sxx.json`. Private
  drafts restore Allow Play and retained Q05. Public imports start as unsaved
  private drafts with Allow Play unchecked; they never adopt the public file
  as the private save target. Public filenames must match the unit ID.
- **Import Reference** deliberately accepts other authoring JSON filenames,
  such as `S01_reference_v2_incomplete.json`. It creates an unsaved private draft
  with Allow Play off; it does not relax the final export filename or validation
  rules. It preserves source language, choice order, accepted labels and empty
  URLs. Use `--reference <file>` to request this import explicitly at startup,
  or `--draft <file>` to open a saved private draft. Neither option auto-exports.
- **Convert v1 to v2** asks for confirmation, then creates an unsaved v2 copy.
  Existing `correctOption` becomes a one-item `correctOptions`; a blank v1
  draft answer becomes `[]`. Retained Q05 is converted too. Original files are
  untouched. Save to a new filename to keep both versions; v1 exports become
  stale relative to a converted source until deliberately re-exported.
- **Open Draft Folder** reads all `S01.draft.json` through `S12.draft.json`
  present in that folder. It reads/checks every file before installing any;
  malformed input or a canceled replacement installs none. Units absent from
  the folder remain in memory. Use individual Load / Import for custom filenames.
- When switching away from an unsaved unit, **Yes** saves, **No** keeps edits in
  memory, and **Cancel** stays on the current unit. Switching never discards edits.
- **New Selected Unit** and replacement imports ask to save unsaved edits first.
  Here **No** discards those unsaved edits; the prompt explicitly says so.
  Saved files are not deleted.
- Closing with unsaved units offers save each / discard unsaved / cancel. A
  failed save or canceled save dialog keeps the application open; any units
  already saved remain safely saved. A crash still loses unsaved memory edits.

Malformed structures that cannot be represented safely (unsupported version,
unknown fields, wrong data types/counts, invalid IDs) are rejected on import.
Missing editable fields receive blank defaults; invalid or incomplete text and
answers remain editable. No authored text is trimmed during private saves.

If an external edit/delete causes a conflict, the existing file is preserved
and your edits remain in memory. Use **Save Draft As** to recover to another
filename, or load the external file after saving your work separately.

## Validate and export

**Validate Unit** uses the versioned shared validator. Strict v1 rules are
preserved; v2 checks nonempty/distinct accepted labels against actual options.
Errors identify the
unit, question and exact JSON field, for example
`S01 / Q03 - $.questions[2].explanationVideoUrl`. Drafts need not pass; final
public exports must. See `data-contract-v1.md` for the recognized URL formats.
Shortened `https://forms.gle/<formId>` links are supported.
No link is visited and no form availability, language or response state is checked.

1. Save private drafts so you can reopen your work.
2. Choose a separate local export folder. Merely choosing it writes nothing.
3. **Export Selected Unit JSON** validates and normalizes the active unit,
   then writes exactly `Sxx.json`. It does not save the private draft or change
   Allow Play. An existing local export requires confirmation before replacement.
4. Mark intended units **Allow Play**. You may mark incomplete drafts locally,
   but the manifest will be blocked until each allowed unit is complete/exported.
5. **Export Public Manifest JSON** checks every allowed source with the same
   Phase 1 validator, rereads its sibling `Sxx.json`, validates that file, and
   compares its normalized public content with the current source. Missing,
   malformed, symlinked, changed or mismatched exports block the entire write.
   Disallowed units need not be complete and are not listed. An empty allowlist
   requires explicit confirmation in the GUI.

Status **Current** means the unit's normalized public data matches that local
file. **Missing** means there is no file in this selected folder. **Stale** means
the source/export is invalid, unreadable or different. Edits to a question,
answer, link, title, or question count can invalidate a previous export. Merely
changing Allow Play, retained Q05 while using four questions, or whitespace that
export normalization trims does not change public unit content. After restarting
the editor, reopen drafts and select the export folder; freshness is established
from the actual files rather than a remembered “exported” flag.

The list refreshes on editing/actions. Manifest export always rereads the files,
even if a background external edit has not yet appeared in the list. Re-export
each changed unit, then regenerate the manifest. Export does not save drafts;
save them separately to retain Allow Play and all private content.

## Local write behavior

JSON uses UTF-8, `ensure_ascii=False`, readable indentation, and a final newline.
The public schema and option order remain unchanged. Writes use a flushed,
fsynced temporary file in the same directory; replacements use `os.replace`.
New files use no-replace rename on Windows and an exclusive hard link on POSIX
to avoid clobbering a concurrently created file. Temporary files are cleaned on
ordinary failures, original targets stay intact on failed replacement, and saved
state is updated only after a successful write.

This is local file conflict protection, not a multi-process locking system or a
guarantee against every filesystem/power-loss failure. Use a normal local
filesystem; unsupported atomic operations fail visibly with edits retained.
There is no automatic backup, autosave or remote synchronization.

Legacy private draft format remains `draftVersion: 1` with exactly
`allowPlay`, `unit` (the editable unit), and `parkedQuestion` (null or retained
Q05). This envelope and all of its answers stay private. It is not a new public
schema version. V2 uses private `draftVersion: 2`, unit `schemaVersion: 2`, and
adds `parkedOptions` for retained D metadata. Mismatched versions/unknown fields
are rejected; migration never happens implicitly. Public manifest remains v1
and can describe valid current exports of either unit version.

## Manual release and desktop checklist

The app ends at local export. Manually upload selected `Sxx.json` files **first**,
then `manifest.json` **last**. Never upload `.draft.json`, a private draft folder,
the source repository, or test fixtures. Removing an entry does not delete an
old server file; manually delete that file if direct access must end. Leave
published units playable for review as desired. Google Forms alone controls
whether submissions are accepted; the editor does not inspect responses.

Before relying on the editor on Windows 11 (and separately on macOS):

1. Launch with your Python/Tk installation; check window sizing, display scaling,
   Unicode font rendering, tabs, keyboard navigation, checkbox/radio keys and wheel.
2. Enter an incomplete unit with multiline/Unicode text. Save/reload it; exercise
   switch Yes/No/Cancel, load replacement, new unit and close cancellation.
3. Edit Q05, choose four, save/reload, then choose five and verify Q05 is restored.
   For v2, select several accepted labels; remove D by choosing three options,
   save/reopen and restore four. Check that text and the D acceptance flag return.
   Clear all accepted labels and verify drafts save but public export is blocked.
4. In a disposable test folder, import the synthetic test units or your own
   locally stored content; validate and export both four- and five-question units.
5. Allow one unit, export its manifest, then edit its answer and confirm manifest
   export is blocked until the unit is re-exported. Test absent files and a newly
   chosen folder too. Uncheck the unit and verify the empty-allowlist confirmation.
6. Check native overwrite/cancel dialogs. Using a disposable copy, modify its
   draft externally and ensure Save refuses it while Save Draft As recovers edits.
7. Validate final exports with `python tools/validate_assignments.py` and review
   video/form content before manually uploading anything.
8. Load a v1 draft, decline conversion once, then explicitly convert a copy.
   Verify that its original file stays v1, including retained Q05. Import the
   supplied S01 reference with Import Reference; preserve its Chinese choices,
   three-option Q05 and empty URLs. Confirm the 11 missing-link errors before
   entering instructor-supplied URLs. Q03 wording remains for instructor review.

The cloud smoke suite uses real Linux Tk widgets under Xvfb but substitutes
native file/message dialogs. It verifies workflow logic, not Windows/macOS native
dialog behavior, DPI, accessibility tooling or platform-specific filesystem behavior.
The student prototype still ignores these exported files until Phase 3 is approved.
