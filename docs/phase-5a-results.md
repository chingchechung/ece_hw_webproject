# Phase 5A — 2D RPG visual enhancement

Implemented on `work`, 2026-10-21. Phase 5A changes the 2D artwork and its
rendering path. **Stop for instructor review before Phase 5B.** No merge to
`main`, production deployment, driving visual changes or gameplay redesign is
part of this delivery.

## Inspection and preservation boundary

Read `AGENTS.md`, `Plan.md`, `README.md`, the Phase 3/4 reports and the existing
CI workflow before implementation. Inspected the student HTML, assignment
loader and game source. The Phase 4 game uses a shared logical maze and player
state, separate 2D/first-person renderers, and a requestAnimationFrame loop.
Its 2D renderer drew visible tiles with many individual Canvas calls, a local
embedded character sheet, terminal/exit primitives and a full-screen vignette.

The Phase 4 2D drawing block was byte-identical to the preserved prototype's
block from `function roundedRect` through just before `function readMapBudget`:
SHA-256 `60f1b4b7a818b98c49fd0272901424cf1004ff3c7ac5d9ebe18908cef2149916`.
The visual suite asserts that hash and substitutes the original drawing block
and sprite into a test HTTP response for paired comparisons. It keeps the same
current student page, assignment, maze seed, camera and zoom. This comparison
does not depend on fetching Git history or modify any deployed files.

Only the old embedded character asset and 2D drawing functions were replaced in
`game.js`. Maze generation, movement speed, collision, player coordinates,
camera calculations, interaction distances, HUD, minimap, answer checks,
loader wiring and the complete driving code remain unchanged. The HTML adds
one local script; its CSS, layout and controls are unchanged. The new renderer
reads shared state and performs no game-state writes. Tests check that repeated
draws leave the maze, player, progress, attempt, camera, zoom and map budget
unchanged. The same seeded first-person frame is also compared as PNG data and
must match Phase 4 **exactly**.

## Original artwork and rendering

All artwork is original procedural Canvas pixel art in
`student/js/rpg-renderer.js`. There are no copied Gather.town assets, external
art downloads, CDN dependencies, new packages, game engine or WebGL requirement.

- **Student:** navy hair/trousers, white lab coat, teal shirt and ochre instrument
  bag/ID. Front, back and both profiles have distinct silhouettes/details. The
  192×160 atlas has four directions, two subtle idle frames and four walking
  phases (two neutral phases share a pose). Walking uses the existing movement
  counter at about eight frames per second. Stopping uses the existing facing
  direction. Integer sprite placement and nearest-neighbor drawing retain crisp
  edges; idle animation does not move the feet or head.
- **Floors:** pale sage laboratory tiles with low-contrast grout, sparse surface
  variation and a painted LAB start mat. No decorative collision objects or
  changes to traversable cells.
- **Walls:** connected steel-blue tops, outlined floor boundaries, southern
  depth faces, consistent corner masks and sparse recessed technical plates.
  Decorations remain inside wall cells. Removing internal wall-top seams makes
  continuous walls and intersections easier to read.
- **Question stations:** original oscilloscope workbenches. Q1–Q5 labels remain
  visible after completion. Amber/waveform marks incomplete stations; mint/check
  marks passed stations. A small two-Hz status light animates incomplete devices.
  Existing proximity state adds restrained brackets and an E badge. The generic
  waveform contains no question or answer information.
- **Finish:** a separate purple EXIT portal with a padlock before completion,
  and a mint arrow/light strip after all questions pass. Its existing E prompt,
  unlock condition and unit-specific Google Form behavior are preserved.

Atlases are built once. A single static floor/wall/start scene is cached for the
current maze and replaced when maze identity changes. Each frame copies only
the visible source rectangle, culls off-screen terminals/exit, then draws the
player and small status indicators. No static scenery is regenerated each
frame. At the largest maze the scene is 1400×1064 (about 5.68 MiB raw RGBA), plus
about 0.37 MiB of sprite/tile buffers, excluding browser/GPU overhead. Drawing
translation is snapped to device pixels without changing camera state.

## Regression results

The complete local runner passed **103 tests, zero failures and zero skips** on
Python 3.12.14, Linux/Cloud Chromium 154.0.8037.57, with an Xvfb display for Tk.
The 98 existing tests are retained; five visual tests were added.

| Suite | Tests | Result |
| --- | ---: | --- |
| Python/schema/model/JavaScript parity/bundle checks | 57 | Passed |
| Tkinter GUI | 16 | Passed |
| Immutable original browser baseline | 4 | Passed |
| Browser JSON validation parity | 1 | Passed |
| Student assignment loading | 12 | Passed |
| Phase 4 gameplay | 8 | Passed |
| Phase 5A visuals and paired measurements | 5 | Passed |
| Assignment CLI: synthetic v1/v2 and empty public manifests | — | Passed |

Commands actually run included `python -m unittest discover -s tests -q`,
`python tests/browser_visuals.py`, and the complete
`DISPLAY=:97 python tests/run_ci.py` using the Cloud Xvfb executable. Also ran
Python compilation, Node syntax checks for the changed/new JavaScript, and
`git diff --check`. The CI equivalent is the existing
`xvfb-run ... python tests/run_ci.py` command. The existing workflow now runs the
visual suite through that runner and uploads its outputs with the other test
evidence, including when a suite fails. Actual post-push workflow completion
must be checked on GitHub; it is not inferred from this local run or YAML.

Existing coverage continues to exercise synthetic v1/v2 assignments, four/five
questions, multiple accepted labels with one student selection, published-unit
allowlisting, invalid JSON, manifest refresh, nested relative paths, switching
and cancellation, map placement/reachability, complete keyboard walking and
driving routes, correct/wrong answers, shrink/restart, cumulative teacher-map
budget, finish links, blur/modal input release, touch and no page scrolling.

New visual assertions cover four distinct character directions, changing idle
and walk frames, retained stop direction, station/finish state differences,
retained Q label pixels, proximity decoration, both zoom levels at all three
viewports, state preservation, a representative intersection and exact driving
pixel parity. The V round trip permits the existing driving code's safe-heading
choice at a wall; it still requires position/progress/camera/map preservation.
The harness checks for JavaScript errors and saves traces/error logs. Rendering
hooks, synthetic assignments and performance probes are test-only HTTP-response
injections, never part of the deployable student bundle.

## Measured performance versus Phase 4

Recorded during the complete local regression run above: Linux Cloud headless
Chromium 154.0.8037.57, device-pixel ratio 1, zoom 150%, seeded 25×19 logical
maze. Each renderer/viewport uses three trials, each with 40 warm-up draws and
120 requestAnimationFrame samples. The workload sweeps the camera by ±28/±18
world pixels with an idle player and animated station lights. Each reported
value is the median of the three trial values; raw trials are in
`test-results/phase-5a/performance.json`.

| Viewport | Phase 4 FPS | Phase 5A FPS | Phase 4 mean draw ms | Phase 5A mean draw ms | Phase 4 p95 draw ms | Phase 5A p95 draw ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1366×768 | 58.1 | 60.0 | 2.120 | 0.052 | 2.8 | 0.1 |
| 1024×768 | 59.0 | 60.0 | 1.579 | 0.047 | 2.4 | 0.2 |
| 390×844 | 60.0 | 60.0 | 0.830 | 0.041 | 1.1 | 0.1 |

The cached renderer reduced measured steady JavaScript drawing-call cost in
this workload. There is an initial preparation tradeoff: atlas generation took
about **4.7 ms**, and the first new scene draw took **20.2 ms**, versus **7.1 ms**
for the Phase 4 comparison's first scene draw. The cached scene also adds the
memory cost described above. Only one scene is retained.

These timings measure CPU-side Canvas command submission, not complete GPU
raster/compositing time. FPS is observed headless browser frame scheduling;
sub-millisecond timings are subject to timer resolution. This short camera
sweep is not a sustained full-game benchmark or proof of performance on an
ordinary physical laptop. Cloud load, fonts, browser build, GPU path, DPR and
display refresh can change results. CI records its own measurements without a
flaky FPS threshold. No Windows, macOS, Safari or native mobile performance
claim is made.

## Visual review artifacts

Inspected generated full-size/small-screen mazes, character directions/walk
sheet, terminal/exit sheet and related screenshots. Adjusted wall seams, label
readability, character details and the unlocked arrow during review.

Two safe synthetic screenshots are committed for review after CI artifacts
expire:

- [1366×768 maze](images/phase-5a-maze.png)
- [Four character directions, idle and walk phases](images/phase-5a-character.png)

The ignored `test-results/phase-5a/` directory is included in the existing
14-day GitHub Actions artifact:

| Review subject | Artifact files |
| --- | --- |
| Paired Phase 4/new views | `before-1366.png`, `after-1366.png`, `before-1024.png`, `after-1024.png`, `before-390.png`, `after-390.png` |
| Character | `character-closeup.png`, `character-directions-walk.png` |
| Station completion | `station-before.png`, `station-after.png`, `stations-finish-states.png` |
| Finish | `finish-locked.png`, `finish-unlocked.png`, `stations-finish-states.png` |
| Navigation | `intersection.png`, `small-screen-175.png` |
| Unchanged driving comparison | `drive-before.png`, `drive-unchanged.png` |
| Performance/debugging | `performance.json`, per-test screenshots, `*.trace.zip`, `*.errors.json` |

All fixture text is synthetic. The site still contains only an empty public
manifest; no instructor drafts, unreleased answers or student information were
copied into the site, committed screenshots or generated test evidence.

## Changed files

| File | Purpose |
| --- | --- |
| `student/js/rpg-renderer.js` | Original character/tile/terminal/exit art, atlases, scene cache and 2D drawing. |
| `student/js/game.js` | Delegate 2D drawing to the visual module; remove superseded embedded sprite and drawing helpers. |
| `student/index.html` | Load the new local visual module before the game. |
| `tests/browser_visuals.py` | Five synthetic visual regressions, artifacts and paired Phase 4 benchmarks. |
| `tests/visual_probe.js` | Test-only deterministic visual staging, sprite/object sheets and timing probe. |
| `tests/run_ci.py` | Run the visual suite with all existing suites. |
| `tests/test_student_bundle.py` | Permit the new local renderer in the strict student-file allowlist. |
| `docs/images/phase-5a-maze.png` | Safe representative full-size synthetic maze screenshot. |
| `docs/images/phase-5a-character.png` | Original character direction/animation review sheet. |
| `docs/phase-5a-results.md` | This implementation, verification, performance and review record. |
| `README.md` | Artwork review, new static asset, visual tests and artifact instructions. |
| `AGENTS.md` | Record authorized Phase 5A and required stop before Phase 5B. |
| `Plan.md` | Record Phase 5A implementation and pending instructor approval. |

The Python GUI, schemas, validators, assignment loader, synthetic JSON fixtures,
public manifests, original prototype/archive and workflow permissions/deployment
policy are unchanged.

## Instructor review and limitations

Download the new push's GitHub Actions artifact using the README instructions
and review `phase-5a/` alongside the two permanent images above. To reproduce
synthetic review artifacts, install the existing development dependencies and
run `python tests/browser_visuals.py`. For interactive local review, serve
`student/` using `python -m http.server 8000 --directory student`. Its empty
manifest intentionally displays no units until the instructor supplies locally
exported public files; do not expose private drafts or copy fixtures into a
production deployment. A manual update must include the new renderer script.

On a real target browser, inspect walking in all directions and stopping at
both zooms, wall/corner readability, incomplete/completed stations, locked and
unlocked exit, touch/small-screen controls, the teacher map, and V out/back.
Review at the device's actual display scaling. Pixel-art appearance remains
subject to instructor approval. Native Windows/macOS/Safari and physical mobile
devices were not exercised in this phase; instructor-reported Phase 4 desktop
testing does not establish Phase 5A platform compatibility. The unchanged
driving artwork is reserved for Phase 5B, which has **not started**.
