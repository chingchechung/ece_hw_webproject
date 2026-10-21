# Phase 5A.2 — adjustable atmosphere and visible interaction sequence

Implemented on `work`, 2026-10-21 (Asia/Taipei). This corrects the deployed
refinement's nearly invisible swipe and overly subtle lighting. The actual
question dialog now waits for an unobstructed animation, and students can turn
all added atmosphere off. **Stop for instructor review before Phase 5B.** No
merge to `main` or production deployment is included.

## Mode defaults, controls and persistence

| Mode | Distant shading | Focus radius at 150% | Question presentation |
| --- | --- | --- | --- |
| Off | None | None | Immediate; original Phase 5A Canvas artwork |
| Normal | 33% blue-gray | 285 CSS pixels / 190 world pixels | 460 ms sequence |
| Strong | 50% blue-gray | 225 CSS pixels / 150 world pixels | 600 ms sequence |

Strong is the default. A valid previously saved `off`, `normal` or `strong`
choice overrides it. Only the string cosmetic preference is stored under
`emi-maze.atmosphere` in localStorage. No unit, question, answer, progress,
player, map budget or student information is persisted. Invalid values fall
back to Strong. If storage is blocked, the in-memory control and game still
work; the choice cannot survive a reload.

The compact desktop HUD selector is synchronized with **2D 氣氛 / Atmosphere**
in the collapsible progress/help panel. At widths up to 1100px the panel offers
the control without adding a HUD row. Both controls have explicit labels.
Changing the mode applies immediately and preserves the current attempt,
progress, camera and zoom; a pending animation is canceled. The controls are
hidden in driving view because they affect only 2D presentation.

Off is checked against the frozen original Phase 5A renderer using exact Canvas
pixel comparison, including completed-question state. It disables new lighting,
new glows, swipe and presentation delay. Original terminal status lights, E
brackets, finish strip and character animation remain part of the original art.

## Stronger light and larger arc

The focus light follows the avatar's torso and uses the same camera transform.
The bright region is smaller in Strong than the previous 200-world-pixel light.
A smooth cached radial opening shades the floor/walls while leaving player,
question labels, terminals and finish bright. Distant passages retain visible
blue-gray detail; they are never made black. HTML text, menus and HUD are not
shaded.

At 175% the nominal Normal/Strong radii are 332.5/262.5 CSS pixels. Radius is
adapted to the smaller viewport dimension, with a minimum of 112 world pixels;
Normal is therefore capped to 304 CSS pixels on the 390px test viewport. The
teacher map remains a separate clear canvas; opening it reduces scene-shading
opacity to 35% of its usual value. The gradient is cached, and a single
quarter-resolution light buffer is rebuilt only for a changed pixel center,
radius, mode or buffer size. It is not a regenerated static maze.

The new original atlas has eight 96×96 frames, cyan/white fronts, a pale-gold
accent and a short fading ribbon. Relative to the previous visible arc, Normal
is about 1.5× and Strong about 2× in size. It rotates for all four facing
directions. The terminal receives a separate brief activation flash below its
Q sign. The arc is clipped around the sign, preserving Q1–Q5 readability. This
is an interaction skill cue with no damage/combat mechanic or collision change.

## Explicit pending interaction and actual modal creation

The 160 ms CSS concealment was removed, rather than lengthened. In Normal and
Strong, pressing E beside an eligible incomplete station creates a small pending
record with the question index, exact maze/unit references, start and reveal
deadline. **No question DOM, answer buttons, modal state or dark backdrop exists
during the animation.** Movement/input and teacher-map countdown pause.

| Sequence part | Normal | Strong |
| --- | --- | --- |
| Preparation / first visible frame | 0–40 ms | 0–80 ms |
| Sweeping energy arc | 40–340 ms | 80–450 ms |
| Station activation flash | 260–420 ms | 300–500 ms |
| Actual question creation target | 460 ms | 600 ms |

A bounded requestAnimationFrame sequence paints the cue. The ordinary frame
loop continues maintaining its time base but skips duplicate drawing while
pending. At reveal, the controller verifies the same pending record, maze,
unit, 2D view, visible document, active attempt and incomplete question. It
consumes the pending record before calling the unchanged question function.
There is no unguarded timeout callback.

Repeated E presses do not start another sequence, and keyboard auto-repeat is
ignored for interaction. Escape, restart, selector/unit switching, view change,
atmosphere change, opening help, blur or hiding the document cancel the pending
frame and transient artwork. An obsolete queued frame cannot clear a newer
interaction. Canceling releases input, repaints the scene and resets the map's
timestamp so pending time is not charged afterward. Confirmed unit replacement
still follows the existing loader validation/confirmation rules.

Off, reduced motion and driving open questions immediately. Reduced motion
allows static lighting but disables the animated arc/new breathing; switching
to reduced motion during a valid sequence reveals the question without waiting
for the skipped animation. Driving physics, renderer and immediate interaction
remain intact. Correct/wrong answers, v1/v2 accepted-label checks, reset/shrink,
station placement, zoom, publishing and the Python editor are unchanged.

## Evidence from real E input

The new suite uses synthetic assignments, deterministic maze seeds, real
keyboard input and the production pending controller. It never calls the
renderer to manually start the accepted temporal sequence.

`strong-E-000ms.png`, `100ms`, `250ms`, `400ms` and `650ms` are captured while
Playwright advances the browser clock through every intermediate animation
frame. The first four have no question/backdrop; the last shows the actual
question. `strong-sequence.json` records target/actual elapsed times, state and
question-opening events. A separate live-clock E test measures ordinary browser
reveal latency and verifies exactly one opening after repeated E.

`interaction-strong.webm` is a short Playwright screen recording of the same
keyboard-driven sequence. Browser-clock control makes the timing screenshots
repeatable; it is not a claim about native hardware frame pacing. There are
also matched Off/Normal/Strong screenshots at 1366×768, 1024×768 and 390×844,
with identical seed, player location, camera and zoom. Mobile shots wait for
the help panel to finish closing.

All generated evidence is in ignored `test-results/phase-5a2/`, automatically
included in the existing CI `test-results/` artifact upload, including failures:

- `mode-{off,normal,strong}-{1366,1024,390}.png` and `mode-comparison.png`.
- `strong-E-{000,100,250,400,650}ms.png`, `interaction-strong.webm` and
  `strong-sequence.json`.
- `live-sequence.json`, `timing-and-freeze.json`, `performance.json`.
- Per-test screenshots, Playwright traces and error JSON; all prior suite
  artifacts remain available too. CI artifacts retain the existing 14-day limit.

Permanent safe images:

- [Matched mode comparison](images/phase-5a2-modes.png)
- [Strong full maze](images/phase-5a2-strong.png)
- [Actual E +250 ms](images/phase-5a2-interaction.png)

No private drafts, instructor questions, unreleased keys or real student data
are present in these artifacts. Both public manifests remain empty.

## Regression strategy

All prior data, GUI, student, gameplay and visual scenarios are retained. The
old test asserting an immediately created but CSS-hidden modal now asserts the
newly authorized pending/no-modal behavior. Control-driven gameplay and touch
helpers wait for completion before inspecting answers; they still traverse the
same real routes and perform all existing answer/finish assertions. Immediate
Off, reduced-motion and driving behavior are checked separately.

Ten new browser tests cover mode defaults/persistence, invalid or blocked
storage, exact Off pixels, measurable Normal/Strong contrast, centered light
across camera/zoom changes, teacher-map softening, real E temporal/video evidence,
live reveal timing, repeated/held E, pause/freeze, all cancellation boundaries,
confirmed unit replacement, reduced motion, immediate driving, matched layouts,
accessible desktop/mobile controls, no scrolling and mode/effect performance.
The browser harness continues rejecting uncaught JavaScript errors.

## Actual test and timing results

The full local runner passed **119 tests, zero failures and zero skips** on
Linux Cloud, Python 3.12.14 and Chromium 154.0.8037.57. The temporary Xvfb
display was stopped after the run. No uncaught page JavaScript errors occurred.

| Suite | Tests | Result |
| --- | ---: | --- |
| Python/schema/model/parity/bundle | 57 | Passed |
| Tkinter GUI | 16 | Passed |
| Original browser baseline | 4 | Passed |
| Browser validation | 1 | Passed |
| Student JSON loading/control compatibility | 12 | Passed |
| Phase 4 full gameplay routes/recovery | 8 | Passed |
| Phase 5A visual checks | 5 | Passed |
| Refinement checks updated for the authorized sequence | 6 | Passed |
| New Phase 5A.2 checks | 10 | Passed |
| Assignment CLI: synthetic v1/v2 and empty public manifests | — | Passed |

The driving Canvas comparison still matches the Phase 4 reference exactly.
Source comparisons also confirm the driving physics/rendering and
question/answer/finish functions are unchanged.

Actual timing evidence from this run:

| Measurement | Result |
| --- | --- |
| Normal reveal, controlled browser clock | 464 ms, target 460 ms |
| Strong reveal, controlled browser clock/pause test | 614 ms, target 600 ms |
| Strong temporal screenshots | Exactly 0/100/250/400/650 ms; no modal at the first four |
| Strong reveal in that temporal sequence | 608 ms |
| Strong live-clock reveal after real E input | About 603–610 ms across full/final focused checks; exactly one question |

The small delay beyond the target is animation-frame scheduling. Pending tests
confirm identical player state and remaining map allowance before/while pending.
Escape also cancels with focus on the zoom selector, and a held E auto-repeat
cannot restart the canceled cue. Confirmed S02→S01 replacement produces a fresh
four-question attempt with no stale modal and a 30-second map budget.
Three focused cancellation/live/timing checks also passed after the final
keyboard-handler cleanup; `live-sequence.json` records the newer 610 ms sample.

Commands actually run included focused atmosphere tests, the full runner,
Python compilation, Node syntax checks and whitespace checks:

```sh
PLAYWRIGHT_BROWSERS_PATH=/tmp/emi-phase5a2-playwright DISPLAY=:97 python tests/run_ci.py
PLAYWRIGHT_BROWSERS_PATH=/tmp/emi-phase5a2-playwright python tests/browser_atmosphere.py
python -m compileall -q tools tests
node --check student/js/game.js
node --check student/js/rpg-renderer.js
node --check tests/atmosphere_probe.js
node --check tests/refinement_probe.js
git diff --check
```

Cloud lacked Playwright's bundled FFmpeg. A temporary
`/tmp/emi-phase5a2-playwright/ffmpeg-1011/ffmpeg-linux` link to installed
`/usr/bin/ffmpeg` enabled development-only video capture; the browser helper
used its existing system Chromium fallback. Standard Playwright Chromium
installation includes FFmpeg for the GitHub runner. No runtime dependency,
cache or binary was added to `student/` or committed.

The unchanged GitHub workflow runs the same full runner, now including the
atmosphere suite, and uploads all generated evidence on success/failure. The
delivery message supplies the verified post-push run URL/status; the table
above records local results and does not infer hosted success.

The first hosted run ([39560552631](https://github.com/chingchechung/ece_hw_webproject/actions/runs/39560552631),
Python 3.12.15 / Playwright Chromium 151.0.7922.34) passed 118/119 tests and
uploaded its evidence. Its sole failure inspected a mid-sequence reduced-motion
change immediately after the browser protocol response while the fake clock
was paused. Media-query change delivery can require the next rendering
opportunity. The test now advances just 32 ms, verifies the preference actually
changed and requires the question to open within those two frames, rather than
waiting for the remaining 500 ms animation. It also verifies that a sequence
was pending first. This corrects test scheduling without changing gameplay or
loosening the normal 460/600 ms reveal checks. All three focused immediate,
freeze/timing and cancellation tests passed after this correction. The final
complete atmosphere rerun also passed all ten tests, including video and
benchmarks, in 117.5 seconds. The final push runs all 119 tests again on GitHub;
its verified result is supplied with delivery.

## Measured performance

The full local run used DPR 1, zoom 150%, a fixed 25×19 maze, synthetic S02,
three trials per renderer/mode/viewport, 40 warm-up draws and 120 RAF samples
per trial. Each value below is the median of the three trial values. The same
camera sweep (±28/±18 world pixels) and nearby incomplete station are used.

| Renderer / mode | Viewport | Observed FPS | Mean draw ms | p95 draw ms |
| --- | --- | ---: | ---: | ---: |
| Previous subtle refinement | 1366×768 | 52.9 | 0.313 | 0.6 |
| Previous subtle refinement | 1024×768 | 60.0 | 0.272 | 0.4 |
| Previous subtle refinement | 390×844 | 59.5 | 0.214 | 0.4 |
| Off | 1366×768 | 60.0 | 0.068 | 0.2 |
| Off | 1024×768 | 60.0 | 0.062 | 0.2 |
| Off | 390×844 | 60.0 | 0.044 | 0.1 |
| Normal | 1366×768 | 60.0 | 0.264 | 0.4 |
| Normal | 1024×768 | 60.0 | 0.255 | 0.4 |
| Normal | 390×844 | 60.0 | 0.195 | 0.3 |
| Strong | 1366×768 | 60.0 | 0.215 | 0.3 |
| Strong | 1024×768 | 60.0 | 0.232 | 0.3 |
| Strong | 390×844 | 59.5 | 0.199 | 0.3 |
| Strong, repeated effects | 1366×768 | 60.0 | 0.288 | 0.4 |
| Strong, repeated effects | 1024×768 | 60.0 | 0.227 | 0.3 |
| Strong, repeated effects | 390×844 | 59.5 | 0.212 | 0.3 |

Off avoids the overlay cost. Normal/Strong remain in the same sub-millisecond
drawing-cost range as the previous refinement in this complete run. The stress
workload directly restarts a renderer effect every 30 sampled frames, about
twice per second; actual gameplay disallows repeated E during its pending
sequence. This stress measures drawing/activation, excluding dialogs and
movement simulation.

Both complete raw trials and an earlier run are retained as `performance.json`
and `performance-preliminary.json`. The earlier run observed Normal at 51.4 FPS
on 1366×768, and Strong on 390×844 at mean 0.352 ms/p95 1.4 ms versus its previous
renderer comparison's 0.182/0.3 ms. Those apparent regressions did not recur in
the full run; they are not discarded. Shared-host scheduling/run variance makes
attribution uncertain, and the lower final means are not a general performance
improvement claim.

These timings measure JavaScript Canvas command submission, not complete GPU
raster/compositing or sustained physical-laptop performance. FPS is observed
headless RAF cadence. Timer resolution, CPU/GPU load, DPR and browser differences
matter. No fixed FPS/no-regression guarantee is made. CI records its own data
without flaky FPS thresholds; real hardware remains for review.

## Memory and comparison baselines

The static scene still retains only the current maze: at most 1400×1064,
approximately 5.68 MiB raw RGBA. Original sprites/tiles add about 0.37 MiB.
The new light opening, glow, eight-frame arc and largest requested light buffer
add at most about **0.82 MiB**, excluding browser/GPU overhead. This is about
0.16 MiB more artwork storage than the previous refinement. Off skips shading,
new glows and cue drawing, though the small shared atlases remain allocated.
No scene/gradient regeneration, unbounded caches, particles or per-frame asset
creation were introduced.

The original Phase 5A renderer remains the Off pixel reference. The previous
refinement from `f80e0e1` is frozen in `tests/fixtures/visuals/phase-5a1-renderer.js`
for performance comparison, SHA-256
`0c9e484cabace70fbde80b5e815f38906a9b5ea8f66dc08fa1f7096e6bf17afd`.
Both are original artwork code with no assignment data, and tests assert their
hashes. Neither comparison renderer is deployed.

## Exact changed files

| File | Purpose |
| --- | --- |
| `student/index.html` | Compact synchronized atmosphere selectors; remove the CSS-only question reveal delay. |
| `student/js/game.js` | Cosmetic preference, guarded pending/RAF sequence, movement/map pause, repeat suppression and lifecycle cleanup. |
| `student/js/rpg-renderer.js` | Three atmosphere modes, stronger adaptive light, larger eight-phase arc/trail and delayed terminal impact. |
| `tests/browser_atmosphere.py` | Ten new mode, timing, cancellation, video, layout and performance tests. |
| `tests/atmosphere_probe.js` | Test-only state/event observations, pixel comparisons and benchmark bridge. |
| `tests/browser_student.py` | Await deferred touch questions and optionally record a synthetic browser test video. |
| `tests/browser_gameplay.py` | Wait for pending presentation before existing route/answer assertions. |
| `tests/gameplay_driver.js` | Expose pending status through the existing test-only state view. |
| `tests/browser_refinement.py` | Retain old scenarios with updated pending/light/lifetime expectations. |
| `tests/refinement_probe.js` | Adapt old probes to the new duration, states and rendering behavior. |
| `tests/fixtures/visuals/phase-5a1-renderer.js` | Frozen previous-refinement performance reference. |
| `tests/fixtures/visuals/README.md` | Comparison provenance/hash and deployment exclusion. |
| `tests/run_ci.py` | Run the new atmosphere suite with every prior suite. |
| `docs/images/phase-5a2-modes.png` | Safe permanent matched-mode comparison. |
| `docs/images/phase-5a2-strong.png` | Safe permanent full Strong view. |
| `docs/images/phase-5a2-interaction.png` | Actual production E sequence at +250 ms. |
| `docs/phase-5a2-results.md` | This implementation, verification, timing and performance report. |
| `README.md` | Current controls, defaults, delays, evidence and test instructions. |
| `AGENTS.md` | Record authorized 5A.2 and cosmetic-only persistence constraint. |
| `Plan.md` | Record the 5A.2 milestone and stop before 5B. |

The Python GUI/model, schemas, shared/deployed validators, assignment loader,
JSON fixtures/manifests, original prototype/archive, development requirements
and CI workflow permissions/upload/deployment policy are unchanged.

## Review and limitations

Review the permanent images and download the new push's GitHub Actions artifact
using the README instructions. Play the WebM in a compatible browser/player and
compare its sequence with the timing JSON. Serve only `student/` for interactive
review, using instructor-exported public files. Update the three changed runtime
files together; never deploy tests, private drafts or the repository root.

Check Off/Normal/Strong on actual target screens, both zooms, map edges,
four facing directions, E/Space/touch, repeated E/Escape, restart/unit selection,
blur/visibility, map time and reduced motion. A foreground browser can reveal
later than the target deadline if its main thread is busy; it must not reveal
early. Hidden/blurred sequences are canceled and require a fresh interaction.

Automated Linux Chromium evidence does not establish native Windows 11,
macOS/Safari, physical touch, display-scaling or GPU compatibility. The
instructor's deployed test concerned the previous refinement. Real-device
visual approval and sustained hardware performance remain for review.
Phase 5B has **not started**.
