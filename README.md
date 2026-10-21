# Digital Electronics EMI Maze Quest

Read [AGENTS.md](AGENTS.md) and [Plan.md](Plan.md) before development.

The offline Tkinter/ttk teacher editor supports S01–S12,
private incomplete drafts, four/five questions, local Allow Play, validated unit
exports and a public manifest containing only allowed units with current exports.
It now creates **v2** drafts with **three/four options per question** and teacher
checkboxes for **one or more accepted answers**. Students choose one answer;
any accepted label passes. V1 files remain editable in their original format;
use **Convert v1 to v2** to create an explicit migrated copy. Phase 3 provides a static
student site supporting both versions. Phase 4 gameplay validation is complete;
Phase 5 awaits instructor review.

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

For authoring references with other filenames, use **Import Reference**. To open
the supplied incomplete S01 reference explicitly at launch:

```powershell
py -3.12 tools\assignment_editor.py --reference "C:\path\to\S01_reference_v2_incomplete.json"
```

Its missing URLs remain empty and block public export. The supplied course
content is private, not a public fixture or Git source. In this development
workspace, the initial private draft is prepared at `teacher_data/S01.draft.json`
(ignored by Git); open it with `--draft teacher_data/S01.draft.json`. Do not copy
that private draft into `assignments/` or upload it. No authoring data auto-loads.

Save and export are separate actions. Manually upload the chosen `Sxx.json`
files **first**, then `manifest.json` **last**. There is no upload/sync function.
Never upload private drafts, the entire repository, or the test fixtures.

See [the editor guide](docs/assignment-editor-guide.md) for four/five-question
editing, unsaved changes, overwrite handling and a manual verification checklist.
Linux/Xvfb GUI regressions passed. The instructor also reports successful
question editing on Windows 11; other native GUI workflows/macOS still need
manual verification.

## Student site — Phase 4

The deployable website is **`student/` only**. It loads the relative
`assignments/manifest.json`, lists only explicitly published S01–S12 entries,
and validates the selected v1/v2 file before starting a fresh attempt. Published
older units remain selectable for practice. Use the HUD unit button to return
to selection; **重新整理清單** refreshes the public manifest without a cache purge.
Opening or refreshing the selector pauses your attempt. Use **返回目前挑戰**,
**取消，返回目前挑戰**, or Escape to resume with the same maze/progress/map time.
Loading a unit while playing requires confirmation; your current attempt is
replaced only after the selected file passes validation. A failed load can safely
return to the current attempt.

```sh
python -m http.server 8000 --bind 127.0.0.1 --directory student
```

Open `http://127.0.0.1:8000/`. The committed public manifest is intentionally
empty: no instructor keys or synthetic assignments are published. For a real
release, manually upload only allowed, validated `Sxx.json` exports to the
website's `assignments/` directory **first**, then upload `manifest.json` **last**.
Upload only `student/` runtime files, never the entire repository, private drafts,
exports or tests. Paths also work when this directory is hosted under a nested
Apache URL such as `/~teacher/course/maze/`; a directory URL must end with `/`,
or use `index.html`.

Four/five-question state, actual three/four options and v2 accepted-label arrays
are retained. One answer button submits one label using the existing validator
helper. Both 2D and driving views, V/E/WASD/arrows, 150%/175% zoom and cumulative
30-second map allowance remain available. Confirmed successful unit loading and
browser reload start fresh attempts. Selector cancel/manifest refresh preserve
the current attempt, while stopping movement and pausing map time. No student
progress is stored across browser reloads. Errors offer retry or safe return.

No build, backend, upload, login or form-management service is needed. Public
JSON is readable by students; it is not secure answer storage. The canonical
shared validators remain in `js/`; byte-identical copies in `student/js/` keep
the deployment self-contained. Update both together: a regression check rejects
drift. The original prototype remains unchanged below.

```sh
python tests/browser_student.py
python tests/browser_gameplay.py
```

This optional Playwright/Chromium suite creates temporary static sites, copies
synthetic fixtures there, tests directory/index URLs and cacheable static JSON,
and removes them afterward. Test hooks exist only in intercepted test responses.
No fixtures or browser-testing infrastructure are included in `student/`.
Phase 4 adds deterministic routes using actual keyboard events and movement
updates, without teleporting. It saves synthetic screenshots, Playwright traces,
state/error logs and placement metrics in ignored `test-results/phase-4/`.
See [Phase 3](docs/phase-3-results.md) and [Phase 4 results/changed files](docs/phase-4-results.md).
Stop for review before Phase 5; no visual-polish phase has started. WebKit could
not be installed because its download hosts return HTTP 403 under the cloud
network policy; Chromium results do not establish Safari compatibility.

## Automated checks on GitHub Actions

Every push to **`work`** runs [Regression tests](https://github.com/chingchechung/ece_hw_webproject/actions/workflows/ci.yml)
from `.github/workflows/ci.yml`. It uses a GitHub-hosted Ubuntu 24.04 runner,
Python 3.12, Node 24, real Tk under Xvfb and Playwright-managed Chromium.
`requirements-dev.txt` pins development-only Playwright, JSON Schema and screenshot
dependencies. The student website and teacher editor retain their existing runtime
requirements. The workflow has only `contents: read`, uses no repository secrets,
and performs no deployment, uploads of course data or server synchronization.

The job runs all Python/schema/model tests, Tk GUI tests, original browser tests,
browser validator parity, student loading tests, Phase 4 walking/driving tests
and the assignment CLI. All required dependencies are checked; skipped tests fail
the CI runner. Independent suites continue after a failure so logs are retained.

To review a run and download evidence:

1. Open the repository's **Actions** tab, select **Regression tests**, then choose
   the run whose branch is `work` and commit matches your push.
2. Open **Ubuntu / Chromium / Python 3.12** to see installation and test logs.
   Confirm the whole job is green, not just a YAML check or browser installation.
3. On the run summary, download the **ubuntu-chromium-python312-…** artifact.
   Artifacts are uploaded even when tests fail and retained for **14 days**.
4. Unzip locally. `ci/summary.json` reports suite exit codes, skipped checks and
   counts; `ci/*.log` contains full command output/tracebacks. Browser folders
   include screenshots, `.trace.zip` traces and `.errors.json` diagnostics;
   `phase-4/` also contains synthetic state and route/placement measurements.
   View a trace with `python -m playwright show-trace <path-to-trace.zip>`.

Only generated `test-results/` is uploaded from a fresh CI checkout. Tests use
synthetic fixtures and temporary drafts; private `teacher_data/`, `export/`, real
student information and instructor answer keys are never artifact inputs. Artifacts
are for regression review, not student-site deployment.

To run the same suite locally on Ubuntu:

```sh
sudo apt-get update
sudo apt-get install -y python3-tk xvfb xauth fonts-noto-cjk
python -m pip install -r requirements-dev.txt
python -m playwright install --with-deps chromium
xvfb-run -a -s "-screen 0 1440x1000x24 -nolisten tcp" python tests/run_ci.py
```

In Codex Cloud, the suite automatically falls back to an available system
`chromium`/`chromium-browser` if the Playwright download is unavailable. To choose
an installed Chromium explicitly, set `EMI_BROWSER_EXECUTABLE=/path/to/chromium`.
A missing override fails clearly. Use the Cloud's available display/Xvfb rather
than assuming `sudo` is available. The browser helper and artifacts stay in `tests/`.

Optional macOS/WebKit strategy (separate from required Ubuntu CI): use a dedicated
macOS runner or developer machine, install Python 3.12 and `requirements-dev.txt`,
then run `python -m playwright install webkit`. Run the four browser scripts with
`EMI_BROWSER=webkit` and no Chromium executable override:

```sh
EMI_BROWSER=webkit python tests/browser_baseline.py
EMI_BROWSER=webkit python tests/browser_validation.py
EMI_BROWSER=webkit python tests/browser_student.py
EMI_BROWSER=webkit python tests/browser_gameplay.py
```

Keep its results/artifacts labelled separately and initially run it manually or
as an optional job; Tk native GUI testing on macOS is a separate desktop check.
Playwright WebKit is not Safari. Even a passing macOS/WebKit run would still need
manual checks in actual Safari (focus, new tabs, input, display scaling and driving)
before claiming Safari compatibility. No macOS/WebKit success is claimed by the
Ubuntu/Chromium workflow, and Phase 5 visual work has not started.

## Original student prototype

The working v1.2 baseline is `emi_maze_dualview_v1.2/index.html`, extracted
byte-for-byte from the supplied ZIP. It remains the fixed-question baseline;
use `student/` for JSON-driven assignments.

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

Optional browser baseline test (development dependencies above and Chromium):

```sh
python tests/browser_baseline.py
```

That test starts and stops its own loopback HTTP server, stubs external video
navigation, and writes ignored screenshots to `test-results/`.

Phase 1 adds [the v1 data contract](docs/data-contract-v1.md), JSON Schemas,
matching Python/browser validators, and a read-only local CLI. The prototype
retains its demo data; the separate `student/` entry point loads unit JSON.
The [v2 contract](docs/data-contract-v2.md) adds versioned multi-accepted-answer
validation in Python and JavaScript while preserving the original v1 schema.

```sh
python tools/validate_assignments.py tests/fixtures/manifest.json assignments/manifest.json
python tools/validate_assignments.py tests/fixtures/v2/manifest.json
python tests/browser_validation.py
```

`tests/fixtures/` contains complete **test-only** S01 (four questions), S02 (five
questions), and a test manifest. `tests/fixtures/v2/` contains separate synthetic
v2 examples, not the supplied course reference. Never deploy these directories.
The public bootstrap manifests in `assignments/` and `student/assignments/`
contain empty allowlists and no unit files.
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
[Phase 2](docs/phase-2-results.md), [Phase 3](docs/phase-3-results.md),
[Phase 4](docs/phase-4-results.md). Development stops for review before Phase 5.
See also the [v2 schema/editor revision results](docs/phase-2-multianswer-results.md).
