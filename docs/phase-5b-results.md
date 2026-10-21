# Phase 5B — laboratory maze driving visuals

Implemented on `work`, 2026-10-21 (Asia/Taipei). The instructor approved all
Phase 5A features, including the slash in a local browser. The remote-desktop
visibility report did not establish a gameplay defect. This phase changes
first-person artwork and preserves that approved 2D implementation.
**Stop after Phase 5B for instructor review. No merge to `main`, deployment,
additional refinement phase or Phase 6 work.**

## Baseline inspection and preservation

The approved driving view already had the widened 14-map-pixel road mask,
axis-separated collision/sliding, stationary steering, DDA wall rays and a
perspective floor. Its floor allocated ImageData and repeatedly queried road
orientation/shoulders every frame. Stations were pole signs; passed signs
replaced their Q identifier with a check. The large windshield pillars and the
question prompt/dashboard overlap reduced the visible driving area.

Before editing, the exact Phase 4 driving-image comparison and the existing
driving collision/control and four/five-question completion tests all passed.
The drawing functions were frozen from approved commit
`b5626bdbc962c98e6aaf10effa148d1d4ed8bc54` in
`tests/fixtures/visuals/phase-5a3-drive.js`, SHA-256
`01bfa3e151cdadf1b8166c97ed2e462600fe0f5f855535fa8ff148e34b3eafc2`.

The existing Canvas functions remain in `student/js/game.js`. Maze generation,
road expansion, ray hits, line of sight, collision, speed/steering model,
interaction eligibility, answers, restart, map budget and loading/input paths
are unchanged. Source-contract tests cover the constants and every gameplay
block outside the driving artwork. In particular:

- 12× virtual driving scale, 590 virtual-unit top speed, 320 acceleration and
  620 braking remain unchanged; reversing and forgiving turning/sliding remain.
- The field of view, 175-unit camera height, continuous 765-unit wall height,
  720-pixel maximum internal width and roughly 30 FPS driving cap remain.
- Rendering reads the authoritative player/road/assignment/progress and stores
  only derived artwork caches. It adds no collision objects or topology changes.
- The **entire** `student/js/rpg-renderer.js` is byte-identical to approved Phase
  5A.3, SHA-256
  `ab8e91df38b8dff681399990d47c3e8b021807fa481b89f0fee90c61a8491667`.
  Off/Normal/Strong, preference persistence, light/shadows, character animation,
  free slash and contextual presentation are preserved.

## Visual design and readability

The palette combines steel-blue laboratory panels, charcoal-blue pavement,
restrained cyan guidance lights, amber incomplete terminals, mint completed
terminals and violet/mint finish states. All assets are original procedural
Canvas artwork. No external images, libraries, engine, WebGL, CDN or build step.

**Roads.** The floor still projects onto the exact widened road mask. Small
world-anchored slab joints/noise give motion cues and fade with projected pixel
footprint/depth to limit shimmer. Gold centre dashes appear only where the
original horizontal/vertical road tests permit them. Narrow cyan shoulders
follow actual road boundaries and stop at openings; they do not reduce the
collision width or invent route arrows. Road flags are cached per 14px subcell:
the original ±56px direction probes equal exactly ±4 subcells. Independent tests
compare those flags and every edge against the live geometry at three offsets
within each open cell, on all four sizes and both question counts.

**Walls/junctions.** The same DDA hits determine the solid wall silhouettes,
corners and openings. Directional face shading, restrained distance fog, panel
seams, continuous cap/waist/base trim and small equipment plates make their depth
and edges easier to trace. Plates are a small part of a wall face, not doors.
Highlights stay on the ray-cast surfaces. Slimmer windshield pillars expose more
of both sides while turning. Distant passages remain readable blue-gray.

**Checkpoints.** Q1–Q5 use cached electronics-terminal artwork with a waveform,
status light and pedestal. Both incomplete and passed states retain the Q label;
passing changes amber to mint and adds a check badge. No question/answer text is
used by the artwork. Each visual pedestal sits up to 18 map pixels toward an
actual road edge, leaving the centre route clear. Its authoritative station and
70px driving interaction radius remain unchanged. Perspective scaling, line of
sight, sorting and per-column wall-depth clipping keep objects correctly ordered
and prevent wide billboards bleeding through nearby corners. Very close sprites
have a bounded screen size for readability; behind-camera objects are culled.

**Finish.** A transparent gantry retains a visible EXIT label and distinguishes
a violet padlock from a mint arrow. The opening remains see-through. Its
eligibility, E requirement and Google Form dialog are unchanged. Passing stations
or the finish never opens a dialog automatically.

**Driving feedback.** World-anchored pavement and wall details move with the
actual position/angle. The lower cockpit has a cropped steering wheel, a speed
strip and N/D/R display, with compact gear letters on narrow screens. Optional
distance-based bobbing is at most 0.65 internal pixels, cockpit sway at most
0.55 pixels and input-based wheel rotation 0.16 radians. No camera roll, motion
blur or physics/inertia changes. Reduced motion disables these optional motions
and fixes status-light brightness. Actual steering still rotates the view.

Screenshot/recording review led to a raised instrument display and a driving-only
prompt position above the HTML dashboard. Mobile prompts retain their existing
clearance above touch controls. These CSS changes are scoped to driving; 2D
layout/appearance is unchanged.

## Regression coverage

The old exact-pixel driving test is adapted to compare frozen/current images
under the same current UI and assert that both leave shared state unchanged.
Its five-test suite remains. The immutable reference is also used for paired
control replays and benchmarks; important regression coverage was not removed.
Separate source checks protect approved physics/2D artwork, and the existing
Off pixel reference, 36 lighting comparisons and real-E slash tests still run.

Two new Python preservation checks and twelve new Chromium tests cover:

- Matched straight, left/right turn, corner, T/four-way, near-wall and checkpoint/
  finish scenes, plus mobile layouts and 2D→drive switching.
- Cached markings against actual geometry on 25×19, 21×15, 17×13 and 13×9 maps,
  with four/five questions; wall depths against the unchanged collision rays.
- Monotonic checkpoint perspective at 140/100/60 map pixels, hidden-object
  rejection, distinct Q1–Q5 labels retained after passing and finish states.
- Identical keyboard-control traces with the frozen/new renderers, including
  acceleration, braking, reversing, steering, collision and unchanged shared data.
- Actual steering/V, reverse/forward gear evidence, reduced motion, teacher-map
  pixel equality/counting and all three screen sizes/both 2D zooms.
- Live browser recording and paired performance at all requested viewports.

The original Phase 4 control-driven routes are unchanged: all v1/v2 × four/five
questions × walking/driving completions, wrong-answer shrink/recovery, restart,
map allowance, cancellation, videos and Google Form flow remain tested. The
JSON validators, Python GUI and assignment loader are unchanged. Fixtures and
all browser hooks remain outside `student/`; public manifests remain empty.

The complete local runner passed **143 tests, zero failures and zero skips**:

| Suite | Passed |
| --- | ---: |
| Python schema/model/source preservation | 59 |
| Tkinter GUI | 16 |
| Original browser baseline | 4 |
| Browser validator parity | 1 |
| Student assignment loading | 12 |
| Phase 4 gameplay | 8 |
| Phase 5A visual | 5 |
| Phase 5A refinement | 6 |
| Phase 5A.2 atmosphere | 10 |
| Phase 5A.3 slash/cache | 10 |
| Phase 5B driving | 12 |
| **Total** | **143** |

All four assignment CLI manifest checks also passed. The browser harnesses
assert no uncaught JavaScript errors; the new tests assert no page scrolling.
Per-suite logs and machine-readable results are in `test-results/ci/`.

Commands actually run include baseline/focused checks and:

```sh
python -m unittest discover -s tests -p test_drive_contract.py -v
PLAYWRIGHT_BROWSERS_PATH=/tmp/emi-phase5a2-playwright python tests/browser_drive.py
PLAYWRIGHT_BROWSERS_PATH=/tmp/emi-phase5a2-playwright DISPLAY=:97 python tests/run_ci.py
python -m compileall -q tools tests
node --check student/js/game.js
node --check tests/drive_probe.js
git diff --check
```

Local tests use Linux, Python 3.12.14, system Chromium 154.0.8037.57 and a temporary
Xvfb display for real Tk widgets. The existing development FFmpeg link in `/tmp`
supports video recording; no dependency/cache/binary is deployed or committed.
The unchanged GitHub workflow runs the whole runner and uploads test evidence
even on failure. Delivery supplies the actual verified post-push URL, test count,
status and artifact link; hosted success is not inferred from local results.

## Performance and memory

The paired benchmark uses the same fixed 25×19 map, pose and viewport for each
renderer, DPR 1, virtual speed 300, yaw sweep ±0.28 radians and position sweep
±10 map pixels. It excludes physics updates to isolate drawing. Each condition
has three trials, 20 warm-up draws and **90 rendered frames** at the existing
32ms minimum draw interval. Values below are medians of per-trial values.
`performance.json` contains every trial, renderer/browser/surface sizes, drawing
and RAF rates, mean/p95 CPU render time and cache byte counts.

Local final full-run measurements (Chromium 154.0.8037.57):

| Viewport | Renderer | Internal surface | Rendered FPS | RAF FPS | Mean draw ms | p95 draw ms |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 1366×768 | Approved 5A.3 | 720×319 | 28.87 | 57.72 | 6.31 | 7.50 |
| 1366×768 | Phase 5B | 720×319 | 29.18 | 58.03 | 5.16 | 6.70 |
| 1024×768 | Approved 5A.3 | 699×419 | 28.87 | 57.41 | 7.74 | 9.30 |
| 1024×768 | Phase 5B | 699×419 | 29.02 | 57.72 | 5.87 | 7.50 |
| 390×844 | Approved 5A.3 | 280×493 | 29.67 | 59.00 | 3.75 | 6.10 |
| 390×844 | Phase 5B | 280×493 | 29.83 | 59.33 | 2.59 | 3.10 |

In these paired samples, mean draw time was lower for Phase 5B at all three
sizes. This supports retaining the caches; it does not establish a general
device performance improvement. Hosted CI produces its own independent data.

Rendered FPS is limited by the preserved driving cap; RAF cadence is recorded
separately. CPU timings measure JavaScript/Canvas command submission, not full
GPU raster/composition, physical laptop refresh or end-to-end gameplay speed.
Timer granularity, tracing, host scheduling and browser load affect short trials.
The measurements are not a general hardware/Safari performance claim.

The renderer reuses a full-height floor ImageData buffer and a per-column depth
buffer. It retains one 1-byte-per-road-cell marker map and at most six derived
objects for the current maze. Twelve cached 96×128 checkpoint/finish canvases
total **589,824 bytes (0.5625 MiB)** raw RGBA. Wall color tables and two gradients
are small and bounded. New maps replace the marker/object cache; resizes replace
the floor/depth buffers. No full-world driving texture or growing history/cache.

Measured Phase 5B buffer dimensions and calculated retained payloads:

| Viewport | Floor bytes | Marker bytes | Depth bytes | Checkpoint RGBA bytes | Total bytes | Total MiB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1366×768 | 918,720 | 7,600 | 2,880 | 589,824 | 1,519,024 | 1.45 |
| 1024×768 | 1,171,524 | 7,600 | 2,796 | 589,824 | 1,771,744 | 1.69 |
| 390×844 | 552,160 | 7,600 | 1,120 | 589,824 | 1,150,704 | 1.10 |

These figures are retained CPU-side payloads and omit native Canvas/GPU/DOM
overhead. The existing output driving surface and approved 2D scene/atlases
remain separate. The former floor allocated a half-height ImageData each frame;
the new fixed buffer trades retained memory for avoiding those repeated
allocations/probes. No claim of measured total-process memory reduction is made.

## Screenshots and real browser recording

All evidence is generated from synthetic S01/S02 assignments. Matched pairs use
the exact same seeded maze, player coordinates, camera direction, viewport and
progress. The old canvas renderer is evaluated in a test-only closure sharing
that state under the current HTML/UI. `scene-poses.json` records every pose and
map/seed counter. No private drafts, unreleased questions or real student data.

Detailed evidence in **`test-results/phase-5b/`**:

| Subject | Files |
| --- | --- |
| Road/junction/wall pairs | `{straight,left,right,corner,t,four,near-wall}-{before,after}.png` |
| Question states | `{station-far,station-near,station-passed}-{before,after}.png`; `station-{140,100,60}-after.png` |
| Finish | `{finish-locked,finish-unlocked}-{before,after}.png` |
| Layout/mode | `small-{before,after}.png`, `viewport-{1366,1024,390}.png`, `switch-2d.png`, `switch-drive.png` |
| Feedback/accessibility/map | `reverse.png`, `acceleration.png`, `reduced-motion.png`, `teacher-map.png` |
| Geometry/state | `road-mask-agreement.json`, `wall-depth-agreement.json`, `station-projections.json`, `checkpoint-labels.json`, `control-replay.json` |
| Video/performance/debugging | `driving-keyboard-demo.webm`, `native-driving.json`, `performance.json`, per-test screenshots, `.trace.zip`, `.errors.json` |

The video uses a real browser clock/production RAF loop on a short route through
a real corner in the seeded maze. Only the initial pose is staged. A controller
sends W/S/A/D keyboard events through the existing handlers; it does not assign
coordinates/speed/angle or call physics updates during the recording. Playwright
sends V, E and Escape. It shows 2D→drive, acceleration, braking to turn, turning,
approaching Q1, stopping about 50 map pixels before it, E's immediate question,
and return to driving. No teleport occurs during the drive. This illustrative
route supplements the unchanged complete control-driven assignment routes.

The final local recording is **13.24 seconds**, 1,272,850 bytes. Its live key
history includes W, S and A; recorded stops occur at the actual corner and Q1
approach. The car reaches zero speed about 51 map pixels before Q1, with the
terminal still visible, all five passes unchanged and the map allowance still
30,000ms. E opens the question without a pending 2D slash; Escape returns to
driving. `native-driving.json` records the route, stop coordinates, keys and
returned state. Hosted CI records a separate run, whose timing can differ.

The entire evidence folder is included in the existing GitHub Actions artifact
with its existing 14-day retention. Videos/traces/fixtures are not committed or
deployed. Permanent safe images:

- [Driving checkpoint](images/phase-5b-driving.png).
- [Matched before/after](images/phase-5b-before-after.png).
- [Checkpoint/finish states](images/phase-5b-checkpoints.png).

## Deployment compatibility

The complete student site is still `student/`, with no additional runtime files.
Upload the changed **`student/js/game.js` first**, then **`student/index.html`**.
Keep the existing scripts and assignment directory together; no automated upload
or server synchronization. The unchanged 2D renderer stays at its approved asset
version to preserve its exact source.

Open **`index.html?v=5b-1`** after the manual update. DevTools Network must show
successful relative requests for `./js/game.js?v=5b-1` and
`./js/rpg-renderer.js?v=5a3-1`. The compatible release markers are:

```js
document.documentElement.dataset.gameRelease // "5b-1"
MazeRpgVisuals.release                       // "5a3-1" (unchanged approved 2D)
```

The existing real-HTTP-cache test primes stale synthetic assets, updates source
and verifies this current compatible pair loads. Existing nested-directory/root
hosting and manifest refresh tests remain. No instructor Apache URL/headers were
provided, so actual server cache/upload verification remains manual. Publish
only allowed validated unit JSON first, manifest last; never upload tests,
the repository root or private `teacher_data/` / `export/`.

## Exact changed files

| File | Purpose |
| --- | --- |
| `student/js/game.js` | Incremental cached road/wall/checkpoint/cockpit artwork, depth clipping, reduced-motion visuals and release marker; preserve all gameplay blocks. |
| `student/index.html` | Versioned game URL, driving-only prompt clearance and background. |
| `tests/browser_drive.py` | Twelve new geometry, rendering, control, accessibility, recording and performance tests. |
| `tests/drive_probe.js` | Synthetic scene setup and read-only observations; controlled render/replay/benchmark and keyboard recording helpers. |
| `tests/drive_reference.py` | Hash-checked frozen driving closure for synthetic test responses. |
| `tests/fixtures/visuals/phase-5a3-drive.js` | Immutable approved pre-5B drawing functions. |
| `tests/test_drive_contract.py` | Two preservation checks covering constants, gameplay blocks, full 2D source and compatible asset URLs. |
| `tests/browser_visuals.py` | Adapt the exact old driving-pixel check into frozen/current image and unchanged-state assertions. |
| `tests/browser_slash.py` | Preserve the existing cache regression with current game/unchanged 2D asset versions. |
| `tests/run_ci.py` | Add the twelve-test driving suite after all existing suites. |
| `tests/fixtures/visuals/README.md` | Golden reference provenance/hash and deployment exclusion. |
| `docs/images/phase-5b-driving.png` | Safe driving checkpoint review image. |
| `docs/images/phase-5b-before-after.png` | Safe matched frozen/current artwork comparison. |
| `docs/images/phase-5b-checkpoints.png` | Safe completed/incomplete and locked/unlocked review sheet. |
| `docs/phase-5b-results.md` | This implementation, measurements, validation and review record. |
| `README.md` | Current artwork, evidence/tests, limits and manual deployment checks. |
| `AGENTS.md` | Record Phase 5A approval and authorized Phase 5B/review boundary. |
| `Plan.md` | Record Phase 5B implementation and remaining instructor/device review. |

The Python GUI/model, schemas, validators, assignment loader, assignment JSON
fixtures/public manifests, dependency requirements, immutable prototype/archive
and GitHub workflow permissions/upload/deployment policy remain unchanged.

## Limitations and instructor review

Linux Chromium automation does not establish native Windows 11 Chrome/Edge,
macOS Chrome/Safari, physical touch/display scaling or integrated-GPU behavior.
Instructor approval of prior gameplay/2D graphics is not a device test of these
new driving visuals. Review the paired images and video on actual target screens,
then drive the initial/minimum maps, turn both directions at narrow/wide junctions,
reverse near walls, approach each Q label, try reduced motion and use the map.
Verify braking to E, V round trips, wrong-answer reset, restart and finish/Form
flow with instructor-exported public assignments.

The preserved ray-column/floor sampling and bounded internal surface can show
pixel edges at high display scaling; this remains a lightweight Canvas 2.5D
view. Billboards have close-range size bounds, and the road geometry/fixed field
of view is preserved. Visual quality, turn visibility and sustained real-laptop
performance still require the requested instructor review.

**Stop after Phase 5B. No further refinement, Phase 6, merge or deployment.**
