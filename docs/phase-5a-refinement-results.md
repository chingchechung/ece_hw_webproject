# Phase 5A refinement — lighting and interaction feedback

Implemented on `work`, 2026-10-21 (Asia/Taipei). The reviewed laboratory artwork
now has broad player-centered focus lighting, a short directional energy swipe,
and restrained station/finish feedback. **Stop here for instructor review before
Phase 5B.** No merge to `main` or production deployment is included.

## Inspection and implementation boundary

Read `AGENTS.md`, `Plan.md`, `README.md`, the Phase 4/5A results and
`.github/workflows/ci.yml`. Inspected the current game, procedural renderer,
animation loop, modal/input paths, map and browser test helpers before editing.
The existing 2D renderer already caches its original character/tile atlases and
one static scene; the game owns movement, shared state, interaction eligibility,
assignment loading and the separate first-person renderer.

Kept that division. The new rendering state consists only of cached light/glow/
swipe images, one small light buffer and at most one transient interaction cue.
It contains no question text, answer labels, external URLs or student data.

Source comparisons confirm maze generation/movement/camera code, teacher-map
functions, driving physics/rendering/frame loop, question rendering/answer checks
and finish behavior are unchanged. Cross-mode switching, modal show/hide, blur
and selector pause now clear transient visual feedback. These small lifecycle
hooks do not modify player position, progress, interaction distance or driving
timing. No schema, GUI, validator, loader, public manifest, original prototype,
dependency or workflow-permission changes were made.

## Lighting and feedback

- **Focus light:** the nearby floor/walls stay bright, while distant scenery
  receives at most roughly 18% blue-gray shading. A cached 256×256 radial opening
  spans a 200-world-pixel radius (300/350 CSS pixels at the two allowed zooms).
  Its center follows the avatar's torso, including camera movement. This leaves
  several nearby corridors visible and keeps distant routes readable.
- **Light buffer:** a single quarter-resolution offscreen Canvas is rebuilt
  only when the light moves by a CSS pixel, zoom or buffer dimensions change.
  The gradient is generated once, not recomputed per frame. The overlay is drawn
  before stations, finish and player, keeping those sprites and labels bright.
  No static scene regeneration, particles, engine, external assets or WebGL.
- **Teacher map:** scene shading drops to 35% of its normal opacity while the
  map is open. The separate map, its controls, 30-second cumulative budget,
  pause behavior and reset rules are unchanged.
- **Interaction:** E, Space and existing click/touch interactions near an
  incomplete question start a clean cyan/white/pale-gold stepped energy arc.
  Six small cached frames rotate with all four facing directions. Duration is
  0.2 seconds; a brief monitor-border activation flash accompanies it. The arc
  clips around the target's Q sign so it cannot obscure the label. No combat,
  damage, weapon or persistent trail is introduced.
- **Modal timing:** the existing question DOM, answer buttons, modal flag,
  input release and map pause are created immediately. CSS holds the visual
  dialog/backdrop reveal for 160 ms, allowing the cue to be seen first. There is
  no delayed question callback, altered eligibility/distance or timer that can
  open a stale question after cancel/reset/switch. Escape and answer handling
  remain responsive during the presentation cue. Driving questions retain
  their immediate appearance and receive no swipe/reveal animation.
- **State feedback:** nearby incomplete terminals have a restrained breathing
  underglow, keeping their Q identity and existing waveform/status light.
  Completed terminals stay calm and retain their check/label. The unlocked
  purple EXIT gets a soft mint pulse; its locked padlock remains distinct.
- **Reduced motion:** the swipe and delayed visual reveal are skipped, and the
  new proximity/exit breathing becomes steady. Existing sprite/status-light
  behavior remains. The preference is read from the browser, with no new menu.

All new art is original Canvas artwork. HUD sizes, layouts, default 150% zoom,
175% option, controls and the reviewed character/floor/wall/station sprites are
retained. Buffers are reused and off-screen station/exit culling remains. New
image buffers plus an overlay bounded by the requested 1366×768 viewport add at
most about **0.66 MiB raw RGBA** beyond Phase 5A, excluding browser/GPU overhead.
The existing largest static scene remains about 5.68 MiB.

## Synthetic tests and review artifacts

The existing 103 tests remain. Six refinement browser tests cover:

1. Light position after avatar/camera movement at both zooms, near/far
   luminance relative to the reviewed renderer, minimum far-scene brightness
   and softened teacher-map shading.
2. Four distinct directional swipe images, the direction of changed pixels,
   expiry after 0.2 seconds and reduced-motion suppression.
3. Actual E input with immediate question/modal state and initially hidden
   presentation in the same keyboard event; repeated E, Escape cancellation,
   eventual reveal and immediate driving dialog behavior.
4. Unchanged Q label pixels during activation, animated incomplete versus calm
   completed terminals, distinct finish states, an actual correct accepted
   answer and four staged directional review frames.
5. Reduced-motion touch interaction, teacher-map display, both zooms, V round
   trip state preservation and small-screen no-scroll behavior.
6. Paired three-viewport Phase 5A/current performance, repeated-action stress
   measurements and before/after/close-up screenshots.

The browser harness continues to reject uncaught JavaScript errors and retain
screenshots, traces and error logs. The five existing visual tests still check
character idle/walk directions, renderer state purity, viewport/zoom behavior,
station/exit states, original Phase 4 comparisons and **exact first-person PNG
pixel parity**. Existing control-driven suites retain v1/v2, four/five questions,
multiple accepted labels, complete walking/driving routes, wrong-answer shrink,
restart, map countdown, unit switching/cancellation and static JSON loading.

For a reproducible comparison, the exact reviewed renderer from `bc7c3fc` is
archived under `tests/fixtures/visuals/`, SHA-256
`fee5cbe020767406b13b7b77df89390773c61e16e01e6eddd31f274e166dc1d8`.
Tests verify that hash and substitute it only in temporary HTTP responses.
The old Phase 4 comparison remains separate. Synthetic probe/fixture code is
never copied into the deployable `student/` directory.

The ignored `test-results/phase-5a-refinement/` directory is included by the
existing CI `test-results/` artifact upload, also on failure, with 14-day
retention:

| Subject | Files |
| --- | --- |
| Full focus-lit views and paired comparisons | `before-1366.png`, `after-1366.png`, `before-1024.png`, `after-1024.png`, `before-390.png`, `after-390.png` |
| Player with focus lighting | `player-focus.png` |
| Directional energy swipe | `swipe-right.png`, `swipe-left.png`, `swipe-down.png`, `swipe-up.png` |
| Question state | `station-before.png`, `station-after.png` |
| Finish state | `finish-locked.png`, `finish-unlocked.png` |
| Map and small screen | `teacher-map-softened.png`, `small-screen-175.png` |
| Performance/diagnostics | `performance.json`, `after-actions-*.png`, per-test screenshots, traces and error JSON |

Swipe screenshots freeze a production-renderer frame at 80 ms through the
test-only bridge; actual E/modal sequencing is tested separately. Some facing
directions use a valid side approach when the fixed maze has no clear approach
on that side. This preserves the game's existing omnidirectional interaction
rule. All screenshots use synthetic S02 data and deterministic seeds. No
instructor drafts, unreleased keys or student information are used. The public
manifest remains intentionally empty.

Two permanent, safe review images are committed:

- [Refined full maze](images/phase-5a-refinement-maze.png)
- [Directional interaction preview](images/phase-5a-refinement-swipe.png)

## Actual regression results

The complete local runner passed **109 tests, zero failures and zero skips** on
Linux Cloud, Python 3.12.14 and Chromium 154.0.8037.57. Tk ran on temporary
rootless Xvfb `:97`, stopped after the run. All 103 prior tests are retained.

| Suite | Tests | Result |
| --- | ---: | --- |
| Python/schema/model/validator parity/bundle | 57 | Passed |
| Tkinter GUI | 16 | Passed |
| Original browser baseline | 4 | Passed |
| Browser validation | 1 | Passed |
| Student loading | 12 | Passed |
| Phase 4 gameplay | 8 | Passed |
| Existing Phase 5A visuals | 5 | Passed |
| New refinement visuals/interactions/performance | 6 | Passed |
| Assignment CLI: synthetic v1/v2 and both public manifests | — | Passed |

Commands actually run:

```sh
python tests/browser_refinement.py
# Focused refinement tests were rerun while developing/reviewing the effects.
DISPLAY=:97 python tests/run_ci.py
python -m compileall -q tools tests
node --check student/js/game.js
node --check student/js/rpg-renderer.js
node --check tests/refinement_probe.js
git diff --check
```

The full runner completed successfully after the final effects and test-helper
corrections. No uncaught page JavaScript errors were reported. Existing tests
also verified exact first-person Canvas pixels against the Phase 4 comparison.
The GitHub workflow runs the same full runner under Ubuntu/Xvfb and uploads the
new evidence automatically through its unchanged `test-results/` upload path.
Its actual post-push completion/result must be checked separately on GitHub;
local success is not used as a substitute.

## Performance relative to reviewed Phase 5A

Measured in the complete local run above at DPR 1, zoom 150%, a fixed 25×19
logical maze and synthetic five-question S02. Each renderer/workload/viewport
uses three trials, each with 40 warm-up draws and 120 requestAnimationFrame
samples. Camera movement is the same ±28/±18 world-pixel sweep with an idle
avatar near an incomplete station. Values are medians of the three trial
values; `performance.json` retains every raw trial.

| Viewport | Reviewed FPS | Refined FPS | Reviewed mean draw ms | Refined mean draw ms | Reviewed p95 ms | Refined p95 ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1366×768 | 60.0 | 60.0 | 0.055 | 0.259 | 0.1 | 0.4 |
| 1024×768 | 60.0 | 60.0 | 0.058 | 0.233 | 0.1 | 0.3 |
| 390×844 | 60.0 | 60.0 | 0.054 | 0.219 | 0.1 | 0.3 |

An additional stress workload triggers a new 0.2-second cue every 30 sampled
frames, about twice per second at 60 FPS, while sweeping the camera:

| Viewport | FPS with repeated cues | Mean draw ms | p95 draw ms |
| --- | ---: | ---: | ---: |
| 1366×768 | 59.5 | 0.296 | 0.4 |
| 1024×768 | 60.0 | 0.269 | 0.4 |
| 390×844 | 59.5 | 0.193 | 0.3 |

The focus overlay has a measurable CPU submission cost: approximately
**0.17–0.20 ms more per normal frame** than the reviewed renderer in this run.
No scheduled-FPS drop was measured in normal exploration; repeated cues stayed
at about 59.5–60 FPS. Trial noise explains why one stress mean is lower than
its normal-workload mean; this is not evidence that extra effects improve
performance. The quarter-resolution overlay retained smooth lighting while
reducing the initial implementation's drawing cost.

These are short headless Canvas command-submission measurements, not complete
GPU raster/compositing times or physical-laptop guarantees. The stress loop
measures the renderer and cue activation, excluding dialog/backdrop display,
question answering and movement simulation. Shared-host scheduling, timer
resolution, DPR, GPU path and browser/font differences affect results. CI
records its own measurements without a flaky FPS threshold. Real-device GPU,
sustained-play and native Safari performance remain unverified.

## Changed files

| File | Purpose |
| --- | --- |
| `student/js/rpg-renderer.js` | Cached focus light, swipe/activation cue, subtle state glows and reduced-motion handling. |
| `student/js/game.js` | Pass map visibility, trigger 2D cues, clear transient feedback at existing lifecycle boundaries; immediate gameplay/modal state retained. |
| `student/index.html` | Scoped 160 ms question presentation animations; no layout/HUD changes. |
| `tests/browser_visuals.py` | Extract reusable visual harness; retain the five existing tests. |
| `tests/browser_refinement.py` | Six new synthetic visual, interaction and performance regressions. |
| `tests/refinement_probe.js` | Test-only pixel sampling, staged review frames and paired timing workloads. |
| `tests/fixtures/visuals/phase-5a-renderer.js` | Frozen reviewed renderer for reproducible comparisons. |
| `tests/fixtures/visuals/README.md` | Baseline provenance, hash and deployment exclusion. |
| `tests/run_ci.py` | Run refinement tests with every existing suite. |
| `docs/images/phase-5a-refinement-maze.png` | Safe permanent focus-light screenshot. |
| `docs/images/phase-5a-refinement-swipe.png` | Safe permanent directional cue screenshot. |
| `docs/phase-5a-refinement-results.md` | This implementation, testing, performance and review report. |
| `README.md` | Current visual behavior, review links and test/artifact instructions. |
| `AGENTS.md` | Record reviewed 5A art and the authorized refinement boundary. |
| `Plan.md` | Record refinement milestone and required stop before 5B. |

## Review and platform limits

Review the permanent images and the new push's CI artifact. Reproduce the
synthetic artifacts with `python tests/browser_refinement.py` using the existing
development dependencies. Serve `student/` locally for interactive review with
instructor-exported public assignments; do not expose private drafts or deploy
test fixtures. Manually update all three changed runtime files together.

On a physical target browser, check light following near map edges and both
zooms, route contrast, all facing directions, E/Space/touch, repeat/cancel/blur,
question label readability, completion/finish feedback, reduced motion, teacher
map and V out/back. Linux Chromium automation does not establish Windows 11,
macOS/Safari, native mobile, physical GPU or display-scaling compatibility.
The user-reported prior desktop play test does not verify this refinement.
Phase 5B has **not started**; instructor review is required before continuing.
