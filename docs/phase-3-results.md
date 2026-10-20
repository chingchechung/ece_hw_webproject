# Phase 3 — student assignment loading

Completed for review on 2026-10-21 (Asia/Taipei), after instructor approval of
Phase 2/v2 and reported successful Windows 11 question editing. Delivery uses
the existing `work` branch. **Stop before Phase 4; no visual improvements started.**

## Result

The static student entry point is `student/index.html`. Only this self-contained
directory belongs on the student web server. The original ZIP and extracted
`emi_maze_dualview_v1.2` remain byte-identical regression baselines. The approved
Python GUI/model, schemas, canonical validators and existing fixtures are unchanged.

- Relative `./assignments/manifest.json` is validated by the existing JavaScript
  validator before presenting any choices. Only explicit S01–S12 entries appear;
  no unit files are fetched until selection, and unlisted filenames are never
  probed. All published units remain selectable for review, without form states.
- Selected files pass `validateUnit(data, entry.file)` before game initialization.
  V1 and v2 retain their actual question objects, option order/counts and answer
  fields. V2 arrays are never flattened to one answer. Each student answer button
  supplies exactly one label to `AssignmentValidator.acceptsAnswer()`; any accepted
  label passes. Question/explanation/form URLs come from the selected unit.
- Returning to selection, refreshing the manifest or selecting a unit clears the
  previous assignment, maze, passed flags, attempt/failure count, player position,
  pending modal, directional input, driving speed/distance/turn/heading and map.
  Successful loading starts at 25×19, zero passes, 2D mode and 30 map seconds.
  There is no carry-over from a previous unit or failed load.
- Missing files, network failures, malformed JSON, unsupported versions, invalid
  fields and filename/ID mismatches leave a useful error in the selector, with
  load retry, another unit and manifest refresh available. Invalid manifests clear
  the allowlist. Aborting superseded requests plus generation checks prevents late
  responses from reviving a previous selection or revoked manifest entry.
- Manifest and unit fetches use `cache: 'no-store'`. Actual cacheable static files
  were updated during tests: refresh and browser reload observe new entries,
  removed entries, changed unit data and empty manifests without a cache purge.
  Assets/JSON work from the server root and `/~teacher/course/maze/`, with both
  directory and `index.html` entry URLs. No root-absolute asset or assignment paths.
- Teacher strings use text APIs or HTML escaping. External video/form links use
  `target="_blank" rel="noopener noreferrer"`. No submissions are recorded and no
  Google Forms availability is inferred. Public assignment answers remain visible
  in JSON, as expected for this static design.

## Gameplay preservation and necessary integration changes

The baseline renderer, sprites, widened two-lane road mask, collision/movement
functions and 12× virtual driving distance remain intact. Both views share the
same current maze/player/stations/progress. V/E, WASD/arrows, touch interaction,
150%/175% zoom, help drawer, modal/blur stopping and cumulative map timing remain.

Question progress and text now derive from the actual four/five-question count;
question dialogs render exactly three/four options. The station candidate check
previously skipped open cells, forcing the fallback for all four stations. The
student copy now selects open candidates in four regions and adds a unique fifth
when needed. All four original maze sizes remain available, with the original
minimum size and randomization strategy.

A wrong choice now immediately creates the smaller attempt and clears all passes,
then displays the existing acknowledgement dialog. Previously the state reset
waited for the next-round button. Manual restart still restores the initial size.
Every fresh unit load (including after a browser reload) starts a new attempt;
the old prototype's page-path localStorage map budget is deliberately not reused
across assignments. Map time still counts only while visible and pauses for
hidden pages, question dialogs or help. The prototype-only simulate-wrong button
is omitted from the student copy.

The unit button and fifth progress marker initially clipped narrow-screen controls.
The functional fix keeps the baseline pill order, shows the compact unit ID on
narrow displays and allows the toolbar to wrap. All original controls remain
reachable, with no whole-page scrolling. This is layout accommodation for loading
and variable question counts; no artwork or renderer redesign was performed.

## Actual verification

Linux, Python 3.12.14, Node 24.19.0, Tcl/Tk 9.0.4, system Chromium through Python
Playwright. Tk tests used the existing rootless Xvfb on `:97`, with no TCP listener;
it was stopped afterward. Native dialogs are mocked, while real Tk widgets and
mainloops run. External video/form navigation is stubbed; no real submissions or
remote course-content requests occurred.

| Command | Result |
| --- | --- |
| `python -m unittest discover -s tests -v` | **48 passed**: all 46 existing schema/model/baseline tests plus two deployment-isolation/validator-drift tests |
| `DISPLAY=:97 python tests/gui_smoke.py` | **16 passed**: eight original v1 and eight approved v2 GUI regressions |
| `python tests/browser_baseline.py` | **4 passed**, original controls/gameplay and 800 original randomized mazes |
| `python tests/browser_validation.py` | **1 passed**, 364 Python/Node/Chromium contract cases and 76 single-choice cases |
| `python tests/browser_student.py` | **12 passed**, detailed coverage below |
| `python tools/validate_assignments.py tests/fixtures/manifest.json tests/fixtures/v2/manifest.json assignments/manifest.json student/assignments/manifest.json` | All valid, exit 0 |
| `python -m compileall -q tools tests` | Passed |
| `node --check student/js/assignment-loader.js` and the other three deployed JS files | Passed |
| `git diff --check` | Passed |

**81 automated tests passed**, with no skipped regression checks. Chromium student
tests cover all four v1/v2 × four/five-question combinations, exact loaded data and
choice counts, single-click acceptance of every label in the synthetic v2 unit,
unit-specific question/explanation/form links, all S01–S12 IDs, unavailable S03,
S01→S02→S01 switching, fresh attempt/drive/map state, invalid/unsupported JSON and
manifests, retries, network failure, overlapping requests and refresh during a load.
The production empty site also runs unmodified, without injected hooks.

The suite generates **1,600 additional mazes** across both versions/counts and all
four sizes, checking station count, uniqueness, open/reachable placement and no
start/finish overlap. It also checks map consume/pause/expiry/restart, 2D/drive
switching with shared position/progress, keyboard movement, E interaction, touch
interaction, input clearing on modal/blur, both zooms and help. No uncaught page
JavaScript errors occurred. Expected HTTP/network errors are exercised explicitly.
At 1366×768, 1024×768 and 390×844, the page neither scrolls horizontally nor
vertically, and essential controls remain within the viewport.

Ignored synthetic screenshots in `test-results/phase-3-2d-{1366,1024,390}.png` and
`phase-3-drive.png` were inspected for layout/control preservation. The new browser
suite serves temporary copies of `student/`, with synthetic fixtures copied only
into those temporary sites; teardown removes them. Test hooks exist solely in
intercepted game-script responses. The deployed directory contains no test code,
fixtures, private drafts, answer examples, Python tools or test dependencies.

## Changed files

| File | Purpose |
| --- | --- |
| `student/index.html` | Static student entry, baseline styles/layout, selector and compact unit HUD; responsive control accommodation |
| `student/js/game.js` | Extracted baseline game with validated assignment initialization, dynamic questions and answer-helper integration |
| `student/js/assignment-loader.js` | Relative fetch, allowlist/validation, retry/refresh UI and stale-response cancellation |
| `student/js/assignment-rules.js` | Exact copy of existing shared URL rules for standalone deployment |
| `student/js/assignment-validator.js` | Exact copy of existing v1/v2 validators and answer helper |
| `student/assignments/manifest.json` | Empty public bootstrap; no real or synthetic unit files |
| `tests/browser_student.py` | Temporary static HTTP sites and synthetic Chromium regressions |
| `tests/test_student_bundle.py` | Exact shared-validator equality and deployment content/privacy boundary |
| `README.md` | Student launch/deployment/test instructions and current phase boundary |
| `AGENTS.md` | Record approved Phase 2 review and stop-before-Phase-4 boundary |
| `Plan.md` | Record approval, Phase 3 selection checks and review boundary |
| `docs/phase-3-results.md` | This report |

The canonical validators stay in `js/`; copies in `student/js/` allow deploying only
one static directory without a build step or parent-directory dependencies. The
equality test fails if they drift. Root `assignments/manifest.json` remains the
unchanged empty Phase 1 bootstrap. No instructor answer keys or private S01 drafts
are staged, committed or copied into the deployable site.

## Instructor review and limits

1. Serve only `student/` over HTTP. Its initial empty-list message is intentional.
2. For local review, manually place allowed, validated exports in the served
   `assignments/` directory, then the public manifest last. Keep private drafts
   outside every served directory and never deploy `tests/fixtures/`.
3. Select S01/S02, return using the unit HUD button and revisit an earlier unit.
   Confirm question titles/videos/choices, single-label acceptance and fresh state.
4. Refresh after manually changing the published manifest. Confirm missing/invalid
   data offers retry, and removed entries disappear. Check V/E, zoom, help, map and
   keyboard controls on the actual target browsers.

Actual Apache, Windows 11 Chrome/Edge, macOS Chrome/Safari, native browser focus,
touch hardware and GPU performance remain untested here. The instructor's Windows
11 GUI-editing verification does not establish student browser compatibility.
Static-server tests establish relative URL/cache behavior, not server configuration
or live video/form availability. Full driving-route completion through every maze
size and the broader Phase 4 gameplay/device acceptance remain for the next phase.
Phase 3 provides their dynamic state/question interfaces and preservation checks;
**no Phase 4 work or visual-polish acceptance is claimed.**
