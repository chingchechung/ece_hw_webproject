# Phase 5A.3 — always-available E-key energy slash

Implemented on `work`, 2026-10-21 (Asia/Taipei). The instructor approved Phase
5A.2 lighting after real-device testing. This change separates the slash from
question proximity and preserves that lighting. **Stop for instructor review
before Phase 5B.** No driving visual work, merge to `main` or deployment.

## Interaction and independent visual state

The previous `interact()` returned immediately without `nearItem`, and the
renderer required a question index to create its effect. Now:

- `beginSlash(maze, time)` creates one visual slash with its direction, start,
  maze identity and cosmetic settings. It takes no question or station index.
- `activateStation(maze, index, time)` adds a separate terminal flash only for
  a valid contextual question interaction.
- The existing guarded `pendingInteraction` remains separate from both visuals.
  A free slash never creates pending/modal state or a hidden backdrop.

E in an empty corridor or beside a completed station plays the slash and keeps
walking/collision/camera updates running. Its origin follows the moving player;
its facing direction is captured when E is pressed. Free E does not alter the
maze, answers, progress, failures or map allowance. A closed map remains at its
existing allowance; an already open map counts its normal viewing time. No
special charge, reset or extra pause was added.

A nearby incomplete question starts the **same** slash, freezes movement and
map countdown, flashes its terminal and reveals its question after the existing
460 ms (Normal) / 600 ms (Strong) deadline. Presses during pending interaction
are ignored. Entering range while a free slash is active does not automatically
open a question: a fresh contextual press starts its own full sequence.

Completed stations remain excluded by the existing nearby-question selection.
Locked finish interactions show the existing reminder and a free slash, without
opening a dialog. An unlocked 2D finish now uses the same guarded presentation
before the unchanged Google Form dialog. Pending finish records use `index:null`
and recheck that all questions passed. Off, reduced motion and driving preserve
immediate question/finish interaction. Driving receives no slash or new delay.

Free deliberate presses can retrigger after **180 ms**. There is only one visual
slash, replaced by a permitted new press; no effect queue or per-press timer.
Keyboard `repeat` is ignored for E/Space. Space, canvas clicks and the touch
button use the same interaction routing. UI wording explains E's 2D energy action;
the touch label returns to the existing interaction wording in driving view.

Escape, restart, selector/unit replacement, blur, document hiding, view changes,
atmosphere changes and opening help clear incompatible visuals/pending frames.
Existing identity and eligibility checks prevent a canceled old callback from
revealing a question or finish. Enabling reduced motion clears a free effect;
an eligible pending interaction reveals immediately without waiting for its
skipped animation. Preference-change tests allow two rendering frames for
Chromium to deliver the media event, not the remaining animation duration.

## Visibility correction without lighting changes

Review of actual E-input images exposed a sprite problem: painting an outline
and core for every point allowed each next dark outline to erase the preceding
white core. It appeared as a striped chain. The atlas now paints each complete
outline/cyan/white layer in order, producing a continuous bright arc, with a
short faded trail, pale-gold tip and brief hand-origin streak.

The eight cached phases sweep across the player's front in four directions.
Normal retains scale 1.1 and Strong 1.5; the effect is not enlarged further.
The opaque core has more contrast with the floor, and the trail fades behind it.
Q signs are clipped out for all nearby stations, including completed ones.
The slash is drawn after the player and scene light. Ordinary redraws retain it;
only expiry or explicit cleanup removes it.

| Part | Normal | Strong |
| --- | --- | --- |
| Preparation / initial visible frame | 0–40 ms | 0–50 ms |
| Main sweeping motion | 40–440 ms: 400 ms | 50–550 ms: 500 ms |
| Terminal activation, contextual question only | 300–450 ms | 400–580 ms |
| Question / eligible finish creation target | 460 ms | 600 ms |

The 33%/50% shade, 190/150-world-pixel radii, viewport/zoom adaptation,
teacher-map softening, gradient, cached light buffer, atmospheric glows and
Off artwork are unchanged. Tests freeze the exact approved `625fd12` renderer
and compare actual full Canvas pixels without an active slash across three
viewport sizes, both zooms, all modes and both teacher-map states: 36 combinations.
The light-gradient and focus-light functions also match the approved source
exactly. The new action allocates no additional Canvas or per-frame texture.

## Genuine keyboard recording and visual evidence

All evidence uses synthetic assignments and deterministic test setup. No course
drafts, unreleased keys or student data are read or recorded. Test hooks observe
events and establish start positions; they never inject a slash frame into the
accepted recording or direction sequences. Real keyboard events start the
production slash/controller, and the real gameplay RAF updates movement.

`test-results/phase-5a3/explore-slash-question.webm` shows:

1. Standing in an empty corridor and pressing E three deliberate times.
2. Walking toward Q1 while pressing E, with no movement freeze or automatic
   question opening.
3. Pressing E within Q1 range; the same slash remains unobstructed until its
   question actually opens.

This recording uses live browser time. A real render-frame observer samples the
visible Canvas once per action, so a later host/protocol delay cannot mistake
an already-finished effect for a missing one. `exploration-recording.json`
records the route, real E/slash/activation/question events and those observations.
Walking uses a bounded real keyboard chord with an automatic key release; it
does not depend on the Python host returning promptly to release movement.
`exploration-start.png` and `real-question-open.png` show the recording's ends.
Controlled-clock `question-slash.png` / `question-open.png` show the exact
unobstructed pre-modal and revealed states. Directional screenshots at **0/120/280/460/620 ms**
are driven by real E and a controlled browser clock through all intermediate
animation frames; they do not claim physical-device frame pacing.

Additional evidence:

- `{right,left,down,up}-{000,120,280,460,620}ms.png` and per-direction close-ups.
- `direction-sequences.json`: visible effect pixels, direction/centroid, expiry.
- `free-versus-question.json`: identical slash-only pixel mask beside the same
  completed/incomplete station at +250 ms; only the latter queues a question.
- `deployment-cache.json`: loaded release markers and relative script URLs.
- `lighting-parity.json`: zero changed pixels in all 36 approved-light comparisons.
- Per-test screenshots, Playwright traces and uncaught-error JSON, including
  failures. Existing suite evidence and benchmarks remain available.

The unchanged GitHub artifact upload includes the whole `test-results/` tree,
with the existing 14-day retention. Comprehensive video/traces remain ignored,
outside the deployable website. Two permanent safe review images are committed:

- [Actual E close-up](images/phase-5a3-slash.png).
- [Four directions from actual E sequences](images/phase-5a3-directions.png).

## Static deployment and cache investigation

The Phase 5A.2 entry page requested unversioned `./js/game.js` and
`./js/rpg-renderer.js`. An HTTP cache could therefore retain one older script
after a manual update. No instructor site URL or Apache response headers were
provided, so stale production assets are a **possible cause**, not a confirmed
diagnosis of the deployed site.

Both changed script URLs now carry the matching relative query **`?v=5a3-1`**.
The game sets `document.documentElement.dataset.gameRelease`, and the renderer
exports `MazeRpgVisuals.release`; both report `5a3-1`. This remains static HTML
and JavaScript, with no build system, CDN, service worker or server changes.

The browser cache regression uses a real cacheable local HTTP server, with all
Playwright routes removed. It primes both previous-version URLs with synthetic
old script bodies, replaces the on-disk scripts, confirms the old URLs still
return cached bodies, then loads the versioned entry page. Both new scripts
execute from matching current versions and a synthetic assignment loads.

Manual deployment verification:

1. Upload the changed `student/js/game.js` and `student/js/rpg-renderer.js`, then
   `student/index.html`. Do not deploy the repository root, tests or drafts.
   Assignment publishing remains the existing manual unit-JSON-first,
   manifest-last process.
2. Visit the course directory's **`index.html?v=5a3-1`** explicitly. This avoids
   an older cached directory/index document that still names old asset URLs.
3. In DevTools Network verify the document and both relative script requests
   succeed, and that game/renderer URLs end in `?v=5a3-1`. Inspect their response
   source/version markers if the uploaded files might be mixed.
4. Evaluate `document.documentElement.dataset.gameRelease` and
   `MazeRpgVisuals.release` in the console. Both must be **`5a3-1`**. A missing or
   different marker indicates an older/mixed source; re-upload the matching files
   and reload that versioned entry URL. Future script edits must bump both query
   tokens and both source markers together.
5. Select a published unit, use Normal/Strong and press E in an empty corridor,
   while walking and beside a question. Check Off/reduced motion, all directions,
   both zooms, Escape/cancellation and driving. Judge visibility on the actual
   laptop display before approving Phase 5B.

## Regression results

The final complete local run passed **129/129 tests, zero failures and zero
skips**, plus all four assignment-CLI validations. No uncaught page JavaScript
errors were recorded. The ten-test slash suite passed in 35.1 seconds in that
complete run. Source comparisons confirmed the protected driving,
question/answer/finish and lighting functions described above are unchanged.

| Suite | Tests | Final result |
| --- | ---: | --- |
| Python/schema/model/parity/bundle | 57 | Passed |
| Tkinter GUI | 16 | Passed |
| Original browser baseline | 4 | Passed |
| Browser validation | 1 | Passed |
| Student JSON loading and controls | 12 | Passed |
| Phase 4 gameplay routes and recovery | 8 | Passed |
| Phase 5A visuals / exact driving parity | 5 | Passed |
| Existing refinement checks | 6 | Passed |
| Existing atmosphere checks | 10 | Passed |
| New Phase 5A.3 checks | 10 | Passed |

The final existing controlled-clock reveal tests measured **464 ms Normal /
614 ms Strong**, and the live real-E question test measured **610.4 ms Strong**,
with exactly one dialog. Direction sequences show visible arcs at 120/280/460 ms
and zero remaining effect pixels at 620 ms. All 36 full-Canvas approved-light
comparisons reported zero changed pixels, including both zooms and map states.

The first complete local run passed 128/129. The sole failure was the native
recording's host-side observation: the trace showed over 600 ms between the
end of a 250 ms wait and its next state query, beyond the 550 ms effect lifetime.
The effect had naturally expired. Moving visibility observations inside actual
render frames and bounding keyboard holds corrected this test race without
extending the animation or altering production code. The complete ten-test
slash suite then passed in 43.5 seconds; all three native free samples contained
over 3,000 changed Canvas pixels at about 152–159 ms, with no pending/modal.
The walking sample recorded actual movement and the contextual sample recorded
pending state with no modal. The resulting WebM was about 8.8 seconds / 679 KB.
The final complete rerun below verifies the correction alongside every old suite.

Commands actually run include:

```sh
python tests/browser_atmosphere.py AtmosphereTests.test_live_e_reveals_once_after_full_sequence AtmosphereTests.test_pending_cancellation_boundaries_and_new_unit AtmosphereTests.test_off_reduced_motion_and_driving_are_immediate -v
PLAYWRIGHT_BROWSERS_PATH=/tmp/emi-phase5a2-playwright python tests/browser_slash.py
PLAYWRIGHT_BROWSERS_PATH=/tmp/emi-phase5a2-playwright DISPLAY=:97 python tests/run_ci.py
python -m compileall -q tools tests
node --check student/js/game.js
node --check student/js/rpg-renderer.js
node --check tests/slash_probe.js
node --check tests/refinement_probe.js
git diff --check
```

Cloud uses system Chromium 154.0.8037.57 and Python 3.12.14, with Tk under a
temporary Xvfb display. Playwright's development FFmpeg uses the existing
temporary `/tmp` link to installed FFmpeg. GitHub uses its standard managed
Chromium/FFmpeg installation and runs all suites on the pushed commit. The final
delivery supplies the verified hosted run URL, conclusion, test count and artifact
link; local results are not treated as proof of hosted success.

## Existing benchmark results

The final local atmosphere benchmark retained its three trials, 40 warm-up draws
and 120 RAF samples per condition at DPR 1 / 150% zoom on the fixed 25×19 maze.
These are medians from `test-results/phase-5a2/performance.json`:

| Strong workload | Viewport | Observed FPS | Mean render ms | p95 render ms |
| --- | --- | ---: | ---: | ---: |
| Ordinary camera sweep | 1366×768 | 60.0 | 0.267 | 0.4 |
| Ordinary camera sweep | 1024×768 | 59.5 | 0.230 | 0.3 |
| Ordinary camera sweep | 390×844 | 59.5 | 0.201 | 0.3 |
| Repeated visual activations | 1366×768 | 60.0 | 0.228 | 0.3 |
| Repeated visual activations | 1024×768 | 60.0 | 0.202 | 0.3 |
| Repeated visual activations | 390×844 | 59.5 | 0.211 | 0.3 |

The repeated workload starts the renderer slash/terminal effect about twice per
second, independently of modal/input handling. Differing trial schedules and
shared-host variance can make repeated-workload medians lower than ordinary
draws; this is not a performance-improvement claim. The initial complete run measured repeated
Strong means of 0.236/0.258/0.275 ms at the same three sizes, also sub-millisecond.
The eight-frame atlas dimensions remain 768×96, about 0.28 MiB raw RGBA as before.
The scene/light/other atlas dimensions and cache bounds are unchanged. Existing
benchmark data also retains all modes and previous-renderer comparisons; it
does not establish physical laptop or full GPU render performance.

## Exact changed files

| File | Purpose |
| --- | --- |
| `student/js/game.js` | Generic free action, shared contextual presentation, finish guard, cooldown, cleanup and executed release marker. |
| `student/js/rpg-renderer.js` | Separate slash/terminal state, moving origin, continuous bright arc/trail and longer visible motion; preserve light code/settings. |
| `student/index.html` | Matching versioned relative script URLs and concise action/control wording. |
| `tests/browser_slash.py` | Ten new real-input, recording, movement, parity, finish, lifecycle and cache regressions. |
| `tests/slash_probe.js` | Test-only observation, deterministic starts, pixel measurements and approved-renderer comparisons. |
| `tests/fixtures/visuals/phase-5a2-renderer.js` | Immutable approved light/artwork reference, SHA-256 `d990d4b61faefb942aafffe90a086f711798b46c343fd27a09e01faaf98c27af`. |
| `tests/fixtures/visuals/README.md` | Reference provenance and deployment exclusion. |
| `tests/browser_student.py` | Match versioned game URLs; opt-in cacheable-script server for the new cache test. |
| `tests/browser_gameplay.py` | Match versioned game URLs; preserve all route/answer assertions. |
| `tests/browser_visuals.py` | Match versioned game URLs for existing visual comparisons. |
| `tests/browser_refinement.py` | Match versioned renderer URLs for existing reference comparisons. |
| `tests/refinement_probe.js` | Adapt existing renderer probes/benchmarks to the separated API while retaining frozen-reference fallback. |
| `tests/run_ci.py` | Add the free-slash suite after every previous regression suite. |
| `docs/images/phase-5a3-slash.png` | Close-up from an actual E-input frame. |
| `docs/images/phase-5a3-directions.png` | Labeled four-direction contact sheet of actual E-input captures. |
| `docs/phase-5a3-results.md` | This implementation, evidence, validation and deployment report. |
| `README.md` | Current controls, evidence, regression command and cache verification. |
| `AGENTS.md` | Record approved lighting and authorized Phase 5A.3 scope. |
| `Plan.md` | Record the Phase 5A.3 milestone and preserve the Phase 5B review gate. |

Python GUI/model, schemas, shared/deployed validators, assignment loader,
JSON fixtures/manifests, dependencies, original prototype/archive and CI workflow
permissions/artifact/deployment policy remain unchanged. The driving renderer
and physics source and question/answer/finish functions match `625fd12` exactly;
only interaction routing/presentation changed. Public manifests remain empty.

## Limitations and review gate

Linux Chromium automation demonstrates behavior, timing, real keyboard input,
pixel equality and captured animation. It does not establish current Windows 11,
macOS/Safari, physical touch, display-scaling or integrated-GPU performance.
The instructor's real-device approval covers the **Phase 5A.2 light**. The new
slash still requires the requested real-device visual/satisfaction review.
Busy foreground frames can reveal a dialog later than its deadline; hidden or
blurred interactions cancel rather than open a stale dialog.

Only one cached atlas/scene/light-buffer set is used per live renderer. The
slash holds constant-size state and follows the existing RAF loop while free;
it adds no independent animation loop or background timer. Contextual sequences
retain their bounded RAF and no pending effect queue. Existing benchmark outputs
record CPU Canvas command cost/headless cadence, not full GPU work or physical
60 FPS guarantees.

**Phase 5B has not started.** Review the WebM, direction sequence, deploy-version
checks and real-laptop readability before approving further visual work.
