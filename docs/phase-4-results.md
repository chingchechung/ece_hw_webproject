# Phase 4 — full gameplay and end-to-end validation

Completed for instructor review on 2026-10-21 (Asia/Taipei), on the existing
`work` branch. Phase 3 was approved. **Stop before Phase 5; no visual enhancements.**

## Result and selector correction

The student site remains the standalone static `student/` directory. It supports
S01–S12 through the public manifest, v1/v2, four/five questions, actual three/four
options and complete accepted-label arrays. Each answer still calls the unchanged
`AssignmentValidator.acceptsAnswer()` helper with one label. No GUI, schema,
validator, instructor content, backend or submission-management changes.

Opening the unit selector now **pauses** the current attempt. It preserves the
maze, player position, question passes, failures, view mode, driving distance and
heading, and remaining teacher-map allowance. Movement/input and speed stop;
the map clock pauses while the selector covers the game. Return/cancel or Escape
resumes the same attempt without restoring held acceleration keys.

Loading a unit while an attempt exists first displays a warning and explicit
confirmation. The existing attempt remains available until the selected file
successfully fetches and validates. Only then does the game replace it and reset
progress, maze, position, failures, driving state and map allowance to 30 seconds.
Choosing the same unit also requires confirmation because it starts a fresh attempt.

Manifest refresh, invalid JSON, missing files and network failures no longer clear
an active attempt. A failed switch offers retry or safe return. Cancel also aborts
an in-flight request; generation checks prevent a late response from replacing
the resumed attempt. If refresh removes the currently loaded unit, the selector
explains that it cannot be reloaded. The student may return to the already loaded
in-memory attempt; no additional request is made for an unlisted file. A browser
reload still starts fresh, with no persistent student progress.

The selector makes the background shell inert, focuses a visible status/control
and restores canvas focus on return. This prevents background keyboard actions
from resetting or moving the paused attempt. Testing found that hiding the
confirmation button during a failed fetch could leave focus outside the selector,
breaking Escape recovery; focusing the loading status fixes that path. Native
Space activation of selector buttons remains usable.

## Gameplay and actual control-driven routes

No driving physics, collision, maze complexity, artwork or rendering changes were
necessary. Both modes retain the same authoritative maze/player/stations/finish,
wide two-lane road mask, forgiving intersections, stationary steering and 12×
virtual distance. The original ZIP and extracted prototype remain unchanged.

`tests/browser_gameplay.py` installs test helpers only in intercepted script
responses. Its route driver never assigns player coordinates, angle or speed.
It finds paths through the actual maze and sends keyboard events through the
game's existing handlers. Every movement uses the real `update(dt)`, including
walking collision and `updateDrive(dt)`. Fixed 1/120-second simulation steps make
long routes repeatable and fast to execute; the browser still renders checkpoints,
dialogs and screenshots. The existing Phase 3 suite retains fast teleport checks,
but the new end-to-end suite installs no teleport helper.

Verified all eight **v1/v2 × four/five questions × walking/driving** completion
combinations. Each first reaches the still-locked finish, then traverses every
question station and reaches the unlocked finish. Tests open question videos,
optional explanations and the selected Google Form via actual new-tab anchor
clicks, with external pages stubbed. V2 deliberately selects a non-first accepted
label when available and renders only three choices where defined.

Walking routes alternate WASD and arrow keys, use E at real arrivals, collide
with the perimeter and verify camera follow/player visibility at both zooms.
Driving routes accelerate with W, brake with S and steer with A/D at junctions,
stopping near stations before E. The initial four/five-question routes cover
hundreds of traversed logical edges and over 170 turns cumulatively. Additional
checks cover reverse from rest, braking reverse with W, stationary left/right
steering, wall collision/sliding, blur stopping and mode switching without moving
the player or changing progress.

Wrong-answer tests first pass a question, then fail another. All passes clear,
the assignment/accepted labels stay identical, the map resets to 30 seconds, and
the sizes progress **21×15 → 17×13 → 13×9 → 13×9**. The tests drive to questions
again after every reset and fully complete the minimum five-question maze in
driving mode. Manual restart returns to 25×19, zero passes and 30 seconds.
Map expiry, pause/resume, selector cancellation with an expired map, and restoration
after restart are covered. Diagonal contact may slide slowly along a wall as in
the original game; releasing throttle stops it. Collision does not require an
unrealistic immediate zero speed during valid tangential sliding.

## Random layout quality and travel assessment

Measured **2,000 deterministic layouts**: 250 seeds for each four/five-question
count at every original size. Every layout has distinct reachable stations,
no start/finish overlap and stations in all four quadrants. Positions and labels
vary. The smallest four-question map has 139 distinct unordered position sets
and 245 labelled layouts among 250 seeds; other sizes/counts have 235–250 position
sets and 250 labelled layouts. Repeated positions on the smallest map are expected
with its limited candidate cells; question labels still vary.

For every open logical cell/adjacent edge, the test independently samples the
widened road mask at 2-pixel intervals, including the car's 6-pixel safety offsets.
All centreline routes have driving clearance, including every junction and the
minimum maze. Real control-driven routes verify that the movement/steering code
can use this clearance, in addition to the graph checks.

The exact shortest tour from start through all stations to finish is computed
over all question orders (at most 120). Distances below are logical neighbour
steps, each 56 map pixels, excluding video/answer time and exploration detours.

| Maze | Four-question median / p95 / max | Five-question median / p95 / max |
| --- | --- | --- |
| 25×19 | 78 / 110 / 122 | 86 / 118 / 142 |
| 21×15 | 66 / 94 / 114 | 70 / 94 / 122 |
| 17×13 | 52 / 76 / 96 | 60 / 80 / 104 |
| 13×9 | 36 / 48 / 52 | 36 / 48 / 60 |

Mean dead-end cells range from **3.0% to 5.5%** of reachable logical cells; mean
dead-end question stations range from **4.4% to 6.6%**. The initial five-question
median is about 28 seconds walking or 98 seconds driving at constant top speed,
before turns/stops; its p95 driving lower bound is about 134 seconds. These
measurements do not show excessive forced dead-end exploration or a need to add
maze complexity. They are informed-route lower bounds, not promises about a
student's search time. Human playability feedback remains useful. The existing
loop rate and Phase 3 station-placement algorithm are retained.

## Actual regression results

Linux, Python 3.12.14, Node 24.19.0, Tcl/Tk 9.0.4 and system Chromium using
Python Playwright. GUI tests use real Tk widgets/mainloops on temporary rootless
Xvfb `:97`; native file/message dialogs are mocked. The display is stopped after
testing. Tests use synthetic assignments only. No real video, form submission,
private instructor answer or student identifier is used.

| Command | Actual result |
| --- | --- |
| `python -m unittest discover -s tests -v` | **48 passed**, existing schema/model/CLI/baseline and bundle checks |
| `DISPLAY=:97 python tests/gui_smoke.py` | **16 passed**, original v1 and approved v2 GUI tests |
| `python tests/browser_baseline.py` | **4 passed**, original game including 800 baseline layouts |
| `python tests/browser_validation.py` | **1 passed**, 364 contract cases and 76 answer cases |
| `python tests/browser_student.py` | **12 passed**, all Phase 3 scenarios retained with the intentional non-destructive selector expectations |
| `python tests/browser_gameplay.py` | **8 passed**, new control-driven completions, switching/recovery, collision/camera, 2,000 layouts and small-screen/map checks |
| `python tools/validate_assignments.py tests/fixtures/manifest.json tests/fixtures/v2/manifest.json assignments/manifest.json student/assignments/manifest.json` | All valid, exit 0 |
| `python -m compileall -q tools tests` | Passed |
| `node --check` on modified/new JS files | Passed |
| `git diff --check` | Passed |

**89 automated regression tests passed.** No uncaught page JavaScript errors.
Expected missing/invalid JSON/network failures are exercised. Existing tests
continue to verify published versus unpublished units, S01→S02→S01 review,
all S01–S12 IDs, relative directory/index URLs, actual static cache refresh and
reload, safe literal rendering of untrusted JSON, and three/four actual choices.
At 1366×768, 1024×768 and 390×844 there is no full-page scrolling, including the
switch confirmation; controls remain usable and paused background input is blocked.

WebKit **did not execute** and is not included in the passing count. The installed
Playwright expects `webkit-2336/pw_run.sh`, which is absent. Attempted:

```sh
PLAYWRIGHT_BROWSERS_PATH=/tmp/emi-phase4-browsers python -m playwright install webkit
```

WebKit 26.5 build 2336 downloads from `cdn.playwright.dev` and
`playwright.download.prss.microsoft.com` both returned **HTTP 403, Domain forbidden**
under the cloud network policy; installation exited 1. No Safari compatibility is
claimed. Actual Windows 11 Chrome/Edge, macOS Chrome/Safari, Apache, touch hardware,
GPU performance and live video/form availability remain untested here.

## Artifacts, local testing and manual deployment

Ignored `test-results/phase-4/` contains a Playwright trace ZIP, screenshot and
state/error JSON for each new test, plus actual-arrival question screenshots,
`walking-routes.json`, `driving-routes.json` and `placement-quality.json`. Artifacts
are synthetic and are not part of the deployment or commit. The final screenshots
were inspected. Inspect a trace locally with `python -m playwright show-trace <zip>`.

Run the commands above from the repository. Browser scripts need the optional
Python Playwright package and `/usr/bin/chromium`; these are development test
dependencies only. No test hook, fixture or browser-testing dependency is needed
by students. Temporary HTTP sites/fixtures are cleaned up by the harness.

For local student review:

```sh
python -m http.server 8000 --bind 127.0.0.1 --directory student
```

Open `http://127.0.0.1:8000/`. The committed manifest is intentionally empty.
For real publication, manually upload allowed validated `Sxx.json` exports into
the deployed `assignments/` first, then `manifest.json` last. Deploy only
`student/`; never serve the repository, private drafts, exports or test fixtures.
Nested Apache directory URLs must end in `/` or use `index.html`.

For instructor review, verify cancel/return while mid-attempt, refresh a manifest,
try a missing/invalid selected file and recover, then confirm a switch and check
fresh state. Walk and drive a four/five-question assignment, try a wrong answer
and restart, use the map until expiry, and check question/explanation/form tabs.
Only Google Forms controls whether responses are accepted; the game has no form
status, grading or submission checks. Public JSON exposes published answer labels.

## Changed files

| File | Why |
| --- | --- |
| `student/index.html` | Return/cancel and explicit switch confirmation controls |
| `student/js/assignment-loader.js` | Pause/resume, validated replacement, recovery/cancellation, manifest preservation and modal focus/background protection |
| `student/js/game.js` | Pause movement/map timer and wire assignment lifecycle; preserve active state until replacement |
| `tests/browser_student.py` | Reusable static-server harness, confirmation helper and corrected Phase 4 preservation expectations for existing scenarios |
| `tests/browser_gameplay.py` | Eight new end-to-end gameplay/recovery/quality scenarios and artifact collection |
| `tests/gameplay_driver.js` | Test-only fixed-time keyboard route driver with read-only player coordinates/angle/speed |
| `tests/placement_quality.js` | Seeded station distribution, graph tours, dead-end and driving-clearance analysis |
| `README.md` | Current selector behavior, test commands, deployment and platform limits |
| `AGENTS.md` | Approved Phase 4 boundary and non-destructive switching rule |
| `Plan.md` | Phase 4 acceptance checks and stop-before-Phase-5 boundary |
| `docs/phase-4-results.md` | This report |

Unchanged: original baseline, Python GUI/model, all schemas, shared/copy validators,
fixtures and both empty public manifests. No instructor keys/private S01 drafts
are published. Phase 5 requires a separate instructor review and approval.
