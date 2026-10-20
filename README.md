# Digital Electronics EMI Maze Quest

Read [AGENTS.md](AGENTS.md) and [Plan.md](Plan.md) before development.

Phase 2 is available: the offline Tkinter/ttk teacher editor supports S01–S12,
private incomplete drafts, four/five questions, local Allow Play, validated unit
exports and a public manifest containing only allowed units with current exports.
It reuses the Phase 1 validator. Student-game integration has not started.

## Teacher editor — Windows 11

1. Install [Python 3.12 for Windows](https://www.python.org/downloads/windows/).
   Keep the installer’s **Tcl/Tk and IDLE** component enabled. No pip packages
   are required for the application.
2. Obtain the repository's **work** branch, keeping `tools/` and `schemas/`
   together. In PowerShell, change to the extracted/cloned project folder.
3. Check Tkinter, close its demo window, then launch the editor:

```powershell
py -3.12 -m tkinter
py -3.12 tools\assignment_editor.py
```

On systems where `python` selects Python 3.12, use
`python tools/assignment_editor.py`. The application needs a desktop display;
it runs locally without a web server or Internet connection.

Keep private drafts in a folder such as
`C:\Users\<name>\EMI Maze Quest\teacher_data`, outside web directories. Use a
separate local export folder such as
`C:\Users\<name>\EMI Maze Quest\export\assignments`. Create/select these folders
in the native file dialogs. The editor does not create or load files on startup.

Save incomplete work with **Save Draft** (`Sxx.draft.json`). Use **Open Draft
Folder** to reopen all twelve standard filenames, or **Load / Import** for an
individual draft/public unit. **Validate Unit** reports exact question/field
errors. Select a local export folder, **Export Selected Unit JSON**, mark the
intended units **Allow Play**, then **Export Public Manifest JSON**. Missing,
changed or invalid exports block manifest generation.

Save and export are separate actions. Manually upload the chosen `Sxx.json`
files **first**, then `manifest.json` **last**. There is no upload/sync function.
Never upload private drafts, the entire repository, or the test fixtures.

See [the editor guide](docs/assignment-editor-guide.md) for four/five-question
editing, unsaved changes, overwrite handling and a manual verification checklist.
Linux/Xvfb GUI tests passed; actual Windows/macOS GUI and native file dialogs
still need manual verification.

## Original student prototype

The working v1.2 baseline is `emi_maze_dualview_v1.2/index.html`, extracted
byte-for-byte from the supplied ZIP. No gameplay migration has happened yet.

Run the original prototype locally:

```sh
python -m http.server 8000 --bind 127.0.0.1 --directory emi_maze_dualview_v1.2
```

Open `http://127.0.0.1:8000/`. Serve only the student directory, never private
draft/export directories or the whole repository on a public server.

Run standard-library tests:

```sh
python -m unittest discover -s tests -v
```

Optional browser baseline test (Python Playwright and `/usr/bin/chromium`):

```sh
python tests/browser_baseline.py
```

That test starts and stops its own loopback HTTP server, stubs external video
navigation, and writes ignored screenshots to `test-results/`.

Phase 1 adds [the v1 data contract](docs/data-contract-v1.md), JSON Schemas,
matching Python/browser validators, and a read-only local CLI. The prototype
still does not load unit JSON; that remains Phase 3.

```sh
python tools/validate_assignments.py tests/fixtures/manifest.json assignments/manifest.json
python tests/browser_validation.py
```

`tests/fixtures/` contains complete **test-only** S01 (four questions), S02 (five
questions), and a test manifest. Never deploy that directory. Public
`assignments/manifest.json` starts with an empty allowlist and no unit files.
`teacher_data/` and `export/` are ignored private local directories; keep actual
drafts outside any served web directory. Validation does not upload or export.

The runtime Python tools use only the standard library. Node runs optional
Python/JavaScript parity tests; the optional `jsonschema` test package checks
the formal Draft 2020-12 schemas. Both checks ran in this environment. Browser
scripts require no npm install, bundler, CDN, or build step.

Real GUI smoke tests (native dialogs are mocked; Tk widgets actually run):

```sh
python tests/gui_smoke.py
# Linux with Xvfb installed:
xvfb-run -a python tests/gui_smoke.py
```

Phase reports: [Phase 0](docs/phase-0-baseline.md), [Phase 1](docs/phase-1-validation.md),
[Phase 2](docs/phase-2-results.md). Development stops at Phase 2 pending instructor
review of the actual GUI workflow.
