# Phase 5B.1 — driving materials and Windows slash compatibility

Implemented on `work`, 2026-10-22 (Asia/Taipei). The instructor reviewed Phase
5B on a Windows computer and requested more realistic materials. The instructor
also confirmed that disabling Windows Animation effects suppressed the 2D slash.
This phase addresses those two requests. **Stop after Phase 5B.1 for instructor
review; no merge into `main`, deployment or unrelated changes.**

## Confirmed cause and slash correction

The renderer rejected `beginSlash()` under reduced motion and cleared the effect
in `drawInteraction()`. Separately, the controller shortened pending interactions
when the media query matched, and its media-change listener either revealed the
dialog early or cleared a free slash. All four paths were reviewed and corrected.

| Game atmosphere | OS/browser motion preference | Explicit slash / contextual reveal |
| --- | --- | --- |
| Off | Either | Disabled / immediate |
| Normal | Either | Enabled / 460ms target |
| Strong | Either | Enabled / 600ms target |
| Driving view | Either | No slash / immediate contextual action |

The game atmosphere determines slash availability. Windows 11 **Settings →
Accessibility → Visual effects → Animation effects OFF** must therefore no longer
silently suppress E in Normal/Strong. The controller always waits for the same
renderer-supplied deadline. Changing the media preference neither clears the
effect nor changes its pending record/deadline. The listener redraws compatible
non-pending views; pending animation keeps its own existing guarded RAF loop.

E still slashes in empty corridors and beside completed stations, follows the
walking character, ignores held-key repeats and does not open a free question.
Nearby incomplete questions use the same slash before their actual dialog;
completed questions stay closed. Finish eligibility, locked reminder and the
unlocked finish sequence remain. Escape, view/unit changes, restart, atmosphere
changes, blur and hiding still cancel safely; identity/eligibility checks reject
stale callbacks. Pending movement/map time remains paused. Driving E is immediate.

Atmosphere Off remains the explicit accessibility control to disable the slash.
Passive terminal/finish pulses and driving bobbing/steering-wheel motion still
respect reduced motion. Spotlight intensity, focus radius, shadow/light mask,
map softening, scene art and atmosphere preference persistence are unchanged.
The approved renderer source is protected after normalizing only the two slash
gates and its release marker. Full lighting pixel comparisons cover **72**
combinations: both OS preferences × three viewports × three modes × both zooms
× teacher map on/off, with no active slash.

## Cached material implementation

`student/js/drive-materials.js` contains original procedural materials, created
once when first entering driving. There are no downloaded textures, image files,
third-party libraries, CDN, WebGL, backend or student build step.

**Walls.** A small 128×128 satin composite/metal panel atlas combines restrained
brushing, broad surface variation, recessed gasket seams, bevels, flush fasteners,
subtle lower-panel wear and a darker wall-floor contact band. Two directional
illuminations and eight mip levels are cached as small RGBA arrays; temporary
Canvas surfaces build the mip chain. The DDA hit coordinate fixes horizontal texture position; the original wall top/bottom
fix vertical perspective. Each unchanged ray column samples its texture strip
into the existing frame buffer. Roof/floor/walls upload together once per frame.
Adjacent mip levels blend continuously as footprint grows; bounded
distance haze softens distant detail. The waist/cap/base trim remains restrained.
The material adds no protrusions, doors or openings.

**Floor.** A 256×256 scalar atlas combines periodic broad epoxy/trowel variation
and small aggregate. Nine averaged mip levels use bilinear sampling and continuous
level blending. Sampling uses actual world position, not frame time or screen
coordinates. World-anchored expansion joints fade below the pixel footprint;
near-wall contact shading derives from the existing road-edge flags. Original
gold road markings and cyan boundaries remain on the same widened road mask.
Floor footprint selection considers both projected axes, including large depth
changes near the horizon. Fine noise is generated only during cache construction.

No geometry, camera/FOV, wall height, road expansion, depth-buffer meaning,
station eligibility, vehicle acceleration/speed/braking/turning/collision or 12×
scale changes. The existing Canvas resolution limits and 32ms driving interval
remain. Source preservation checks normalize only the authorized slash scheduling
changes; every other gameplay block still matches its approved hash. The original
Phase 4 control-driven complete routes and all Phase 5B geometry tests remain.

The Phase 5B renderer/cache functions are frozen from reviewed Phase 5B commit
`11b0cdfab1ceb3df9a87e34183d3965e1d4870de` in
`tests/fixtures/visuals/phase-5b-drive.js`, SHA-256
`30b43edfffbc7c12b4bf2044ef1689c4ddaba775a7a8aff9d2634f5a30f9186d`.
Its private derived cache shares the current unchanged physics/state for matched
poses and timings. The older 5A.3 reference remains separately operational.

## Regression results

The final complete local runner passed **151 tests, zero failures, zero skips**:

| Suite | Passed |
| --- | ---: |
| Python schema/model/source/bundle | 59 |
| Tkinter GUI | 16 |
| Original browser baseline | 4 |
| Browser validator parity | 1 |
| Student assignment loading | 12 |
| Phase 4 gameplay | 8 |
| Phase 5A visual | 5 |
| Refinement | 6 |
| Atmosphere | 10 |
| Slash/cache/preference | 13 |
| Driving visual/control | 12 |
| New materials | 5 |
| **Total** | **151** |

All four assignment CLI manifest checks passed. Browser harnesses reported no
uncaught JavaScript errors or capture errors; layout checks found no page scroll.
`test-results/ci/summary.json` and per-suite logs record the complete result.

The five new material checks cover matched frozen/current scenes, state
preservation, cached data stability through real keyboard movement/turning,
periodicity/filtering, all maze sizes, true DDA depths/road flags, sampled
temporal aliasing, three viewports/no page scrolling, performance and a live
production driving recording. Original control-driven routes still complete
v1/v2 × four/five questions × walking/driving; resets, restart, map budget,
unit switching, answer semantics, videos and Forms remain tested.

Three added slash tests check preference changes with original pending deadlines
and real-clock E videos under both preferences. Existing slash/refinement/
atmosphere tests now require a visible reduced-motion slash; Off/driving immediate
paths remain. The six-way atmosphere/preference matrix checks actual effect pixels.
No duplicate question, lost passes or map charge during pending sequences.
The cache test primes stale synthetic scripts and verifies all three current
release-marked scripts load through real relative HTTP requests. Bundle isolation
allows only the new static material module; no fixtures enter the student site.

Commands actually run include:

```sh
python -m unittest discover -s tests -v
PLAYWRIGHT_BROWSERS_PATH=/tmp/emi-5b1-playwright python tests/browser_slash.py
PLAYWRIGHT_BROWSERS_PATH=/tmp/emi-5b1-playwright python tests/browser_materials.py
PLAYWRIGHT_BROWSERS_PATH=/tmp/emi-5b1-playwright DISPLAY=:97 python tests/run_ci.py
python -m compileall -q tools tests
node --check student/js/drive-materials.js
node --check student/js/game.js
node --check student/js/rpg-renderer.js
node --check tests/material_probe.js
git diff --check
```

Focused slash/spotlight and geometry tests were also run before the full runner.
An initial test helper used a nonexistent map method and was corrected to the
existing helper. The bundle allowlist was updated explicitly for the new module.
An imported TestCase initially caused duplicate discovery in the new suite; the
module import now avoids that, and the final runner executes five material tests.

Linux tests use Python 3.12.14, system Chromium and real Tk under temporary Xvfb.
The development-only `/tmp` FFmpeg link supports Playwright recording. No tool,
temporary dependency, test hook or recording is deployed. The unchanged GitHub
workflow runs the entire suite and always uploads `test-results/` with 14-day
retention. Delivery reports the actual post-push run URL, count and conclusion.

## Performance and memory

The benchmark compares frozen Phase 5B with Phase 5B.1 using the same seeded maze,
pose, DPR 1 and viewport. It uses speed 300, yaw ±0.28rad, position ±10 map pixels,
20 warm-up draws and 90 rendered frames/trial, three trials/renderer/viewport.
The existing 32ms drawing interval is preserved; physics is excluded to isolate
drawing. The table uses medians of per-trial values, not a pooled percentile.

Final complete local run, Chromium 154.0.8037.57:

| Viewport | Renderer | Internal surface | Rendered FPS | RAF FPS | Mean draw ms | p95 draw ms |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 1366×768 | Phase 5B | 720×319 | 28.87 | 57.08 | 5.12 | 6.60 |
| 1366×768 | Phase 5B.1 | 720×319 | 29.02 | 57.07 | 6.34 | 9.00 |
| 1024×768 | Phase 5B | 699×419 | 29.18 | 57.38 | 6.13 | 10.10 |
| 1024×768 | Phase 5B.1 | 699×419 | 28.87 | 57.41 | 6.83 | 8.40 |
| 390×844 | Phase 5B | 280×493 | 29.83 | 59.33 | 2.68 | 3.40 |
| 390×844 | Phase 5B.1 | 280×493 | 29.83 | 59.33 | 2.75 | 3.40 |

Material detail adds measured mean drawing cost of **1.21ms / 0.70ms / 0.08ms**
at the three sizes. The rendered cadence remains about 29–30 FPS under the
preserved cap. This is a bounded CPU/memory tradeoff for materials, **not a
performance improvement**. The lower sampled 1024px p95 is not a general speedup
claim. Sustained performance on ordinary student hardware remains a device check.
Every trial and actual browser/surface size is saved in `performance.json`.

The first implementation measured roughly 19–21ms desktop mean drawing cost
and 26 rendered FPS. Profiling identified repeated modulo operations in floor
sampling and expensive per-column native Canvas texture submissions. Power-of-two
wrapping now uses bit masks; bilinear/trilinear wall samples use the existing CPU frame buffer, with
2×2 blocks and one final image upload. A tiny cached roof-color row table replaces
the former gradient submission. Geometry, physics and the frame interval are
unchanged. Preliminary full runners were stopped for those optimizations; only
the final complete run is the acceptance result.

Timings measure JavaScript/Canvas submission, not full GPU raster/composition,
physical display pacing or native laptop performance. Browser scheduling/tracing
and timer granularity affect short runs. RAF cadence is reported separately from
the approximately 30 FPS rendered cadence; no Safari/hardware improvement claim.

Material cache payloads:

| Cached data | Raw bytes |
| --- | ---: |
| Floor scalar mip levels, 256² through 1², Float32 | 349,524 |
| Two wall illuminations, 128² through 1², RGBA | 174,760 |
| **Total additional material payload** | **524,284 (about 0.50 MiB)** |

The existing floor/output/depth buffers, road flags and checkpoint atlas remain
separate; native Canvas/GPU/JS overhead and temporary atlas-construction buffers
are not included in this payload calculation. The material cache is reused across
frames, maze changes and resizes. It does not allocate a full-world texture or
retain a history of worlds. Texture pixel data has no disk/network asset size.

New static source asset: **`student/js/drive-materials.js`, 4,111 bytes** UTF-8.
There are zero new texture-image/download assets. Changed runtime files are
`game.js` (51,555 bytes), `rpg-renderer.js` (20,223 bytes), and `index.html`
(27,189 bytes); no runtime dependency was added. The small roof row-color table
adds four bytes per internal surface row (about 1.3–2.0 KiB at tested sizes).

## Visual and recording evidence

All screenshots, traces and videos use deterministic **synthetic** assignments.
No private teacher drafts, unreleased answers or real student information are read.
Before/after images use identical positions, directions, maze/progress and viewport;
the frozen renderer executes in a test-only closure under the current shared UI.

`test-results/phase-5b1/` contains:

- `{straight,near-wall,long,left,right,four,station-near}-{before,after}.png`.
  The near-wall pair is a close corner approach showing both wall and floor;
  the original nose-to-wall collision/depth checks remain in the old suite.
- `viewport-{1366,1024,390}-{before,after}.png`, recorded `scene-poses.json`.
- `{near-wall,long,station-near}-native.png`: actual internal drive surfaces,
  saved at native resolution without resampling or compositing material sprites.
- `texture-stability.json`, `texture-memory.json`, `geometry-filtering.json`,
  `performance.json`, per-test screenshots/error logs/traces.
- `materials-driving.webm`, `native-driving.json`: a live production-clock route
  with forward driving, braking, a corner turn, approach/stop/E and return. Only
  the initial pose is staged; W/S/A/D pass through existing keyboard handlers,
  V/E/Escape use Playwright input. No position/angle/speed assignment or direct
  physics stepping occurs during the recorded drive.
- `slash/`: Off/Normal/Strong × both system preferences screenshots and pixel
  results; preference-change deadline/map observations; `slash-reduce.webm` and
  `slash-no-preference.webm`, plus live action/pixel/dialog event JSON. These
  recordings use actual E and production RAF/renderer/controller, showing free
  Strong/Normal slashes followed by a contextual Strong slash/question/return.

The final local six-way slash matrix reported **zero** effect pixels for Off
under either preference, over 2,100 for Normal and over 4,200 for Strong. All
72 no-slash lighting comparisons reported **zero changed pixels**. Live Strong
question delays were **602.2ms no-preference / 610.6ms reduced**, with visible
free/contextual effects and exactly one question in each recording. Changing
the preference in either direction retained Normal/Strong deadlines (observed
reveals 464–468ms / 608–612ms) and the original map budget/progress.

The reduced-motion slash recording is **6.12s / 578,117 bytes**; no-preference is
**5.84s / 559,948 bytes**. These are real browser-clock recordings, independent
of the controlled-clock sequence screenshots. Hosted CI records separate clips.

The final local driving clip is **14.12s / 1,343,668 bytes**. Review shows forward
motion, braking, a left corner, wall/floor materials following world geometry,
Q1 approach/stop, E and return. Cache observations found unchanged wall hashes
and floor samples across movement/turning, reused material identity and zero
world wall-coordinate anchor error. Four-size subpixel-motion samples had zero
stationary changes, maximum mean RGB-channel delta **0.154/255**, p95 **1/255**,
and fewer than **0.073%** of sampled pixels changing by more than 30 levels.
These bounded samples supplement the recordings; they are not a universal
flicker-free or physical-display guarantee.

Three representative safe images are permanent review artifacts:

- [Matched material comparison](images/phase-5b1-comparison.png).
- [Native-resolution wall/floor material frame](images/phase-5b1-native.png).
- [Actual E slash with simulated Windows animation disabled](images/phase-5b1-reduced-slash.png).

## Manual Apache update and verification

Upload these **three scripts first**, keeping the rest of the `student/` bundle:

1. `student/js/drive-materials.js` — new original procedural material module.
2. `student/js/game.js` — material integration and corrected pending/media handling.
3. `student/js/rpg-renderer.js` — corrected slash gates.
4. Upload `student/index.html` **last**, requesting all three scripts with
   `?v=5b1-1`.

Open `index.html?v=5b1-1`. DevTools Network must show successful relative requests
for all three scripts, including under the course subdirectory. In Console:

```js
[document.documentElement.dataset.gameRelease,
 MazeRpgVisuals.release, MazeDriveMaterials.release] // ["5b1-1", "5b1-1", "5b1-1"]
document.querySelector('#atmosphereSelect').value    // "off", "normal" or "strong"
matchMedia('(prefers-reduced-motion: reduce)').matches
```

On the instructor's Windows 11 browser, turn Animation effects OFF, choose
Normal/Strong and press E in a corridor and near Q1. The slash must remain visible
and contextual dialogs must wait for it. Switch Animation effects while a slash
is running, then check Off's explicit disable behavior. The existing spotlight
must look unchanged. Driving must retain reduced passive motion with this setting.

Publishing remains validated allowed unit JSON first, manifest last. Never upload
the repository root, tests, private drafts or recordings. No automatic deployment
or synchronization was added. No Apache URL/cache headers were supplied; actual
server cache/upload verification remains the instructor's manual check.

## Exact changed files

| File | Purpose |
| --- | --- |
| `student/js/drive-materials.js` | New original cached material generator/mips and floor sampler. |
| `student/js/game.js` | Material projection/single-buffer drawing, unchanged ray depths/physics, corrected pending/media handling and release marker. |
| `student/js/rpg-renderer.js` | Remove only the two reduced-motion slash suppressions; update release marker. |
| `student/index.html` | Add relative material script and synchronize all three asset query versions. |
| `tests/browser_materials.py` | Five matched material/geometry/stability/filtering/performance/live-recording tests. |
| `tests/material_probe.js` | Test-only synthetic pose, native frame, cache/world-anchor and sampled aliasing observations. |
| `tests/fixtures/visuals/phase-5b-drive.js` | Immutable Phase 5B drawing/cache reference. |
| `tests/drive_reference.py` | Verify reference hash and provide its test-only closure. |
| `tests/browser_drive.py` | Name current/frozen benchmark renderers accurately and reuse its established benchmark/recording methods. |
| `tests/browser_slash.py` | Preference matrix/deadline tests, two real E videos, 72 lighting comparisons and all-three-script cache check. |
| `tests/browser_atmosphere.py` | Replace obsolete reduced-motion bypass expectation with preserved sequence/deadline coverage. |
| `tests/browser_refinement.py` | Require visible/expiring reduced-motion slash and delayed touch interaction. |
| `tests/test_drive_contract.py` | Normalize only authorized slash changes before protecting the remaining source; require matching asset URLs. |
| `tests/test_student_bundle.py` | Explicitly allow the new static module while retaining deployment/privacy isolation. |
| `tests/run_ci.py` | Add the five material tests after every existing suite. |
| `tests/fixtures/visuals/README.md` | Reference provenance/hash and updated source-preservation scope. |
| `docs/images/phase-5b1-comparison.png` | Safe same-pose Phase 5B/5B.1 review sheet. |
| `docs/images/phase-5b1-native.png` | Safe native-resolution production material frame. |
| `docs/images/phase-5b1-reduced-slash.png` | Safe real E frame with reduced-motion simulation. |
| `docs/phase-5b1-results.md` | This design, cause, correction, measurements, evidence and review record. |
| `README.md` | Current behavior, evidence, commands and exact manual deployment/console checks. |
| `AGENTS.md` | Record authorization, confirmed Windows issue and Phase 5B.1 stop boundary. |
| `Plan.md` | Record requested refinement, completed implementation and remaining review/device checks. |

The Python GUI/model, JSON schemas/validators/loader, public manifests, synthetic
assignment contents, original prototype and workflow permissions remain unchanged.

## Limits and review boundary

Chromium media emulation reproduces the browser preference, not the Windows
Settings UI or native hardware. The instructor should retest both settings on
Windows 11 Chrome/Edge, inspect materials while driving/turning/reversing on an
ordinary integrated-GPU laptop, and check minimum/initial maps, Q1–Q5, finish,
both zooms and mobile controls. macOS Chrome/Safari and physical touch/DPI checks
remain unverified; Linux Chromium success does not establish Safari compatibility.

The retained low-resolution Canvas approach, including 2×2 material sampling and Canvas size cap can show
pixel edges at large display scale. Detail filtering reduces shimmer; sampled
aliasing checks and a short recording do not prove every pose/device flicker-free.
Lighting is baked/distance shaded, with no physical reflections or dynamic shadows.
Material realism/readability and sustained native performance need instructor
review. **Stop after Phase 5B.1.**
