# 3D-P2 — Educational assignments and the 2D car

P2 continues approved **`7902de5f89a9c6d182bc5cc836603de5b7cc85b0`** on
**`feature/3d-showcase`**. The instructor approved physical P1.1 navigation.
This phase adds the original procedural car and the approved educational rules;
it does not change the 3D materials, lighting, quality presets, camera controller
or driving equations. **Stop after P2 for instructor review. No merge into
`work`/`main` and no next graphics/gameplay phase.**

## Assignment architecture and parity

`src/assignments/validator.js` imports the **actual** unchanged Lite
`AssignmentRules` and `AssignmentValidator` modules. Esbuild bundles their UMD/
CommonJS implementations behind this isolated adapter. There is no second
validation algorithm. Manifest/unit validation, normalization and
`acceptsAnswer()` are the approved implementations. Parity tests compare module
identity and browser-UMD outcomes, including malformed fields, versions, URLs,
option counts, accepted arrays and invalid student selections.

`PublishedAssignments` resolves `./assignments/` against `document.baseURI`.
It fetches a no-store version-1 manifest and only a filename explicitly listed
there. Manifest validation restricts S01–S12 and matching Sxx filenames; the
game never guesses other unit files. Unit validation precedes normalization and
activation. Public v1 and v2 retain their option order, three/four options as
applicable, and all accepted labels. Students click **one** labelled answer
button. The model calls the actual `acceptsAnswer()`; any accepted label passes.
Arrays and nonexistent labels are not accepted as student selections.

The native-modal selector pauses the vehicle and full-map clock. It keeps the
current attempt while refreshing/choosing. A new attempt requires confirmation,
then successful loading/validation. HTTP errors, malformed/unsupported JSON,
invalid manifests and cancellation leave the old attempt available. Abort plus
a generation token reject canceled/superseded responses, even when a test fetcher
ignores abort. Empty manifests show a clear message; there is no silent demo
fallback. Safe DOM text renders teacher strings without executing HTML.

**3D Demonstration Mode** remains the explicitly labelled, offline five-LAB
experience with no official questions or Form. **Educational Assignment Mode**
is entered only with a validated public unit. The two modes share the renderer,
physics and state lifecycle. Educational play hides and guards unlimited
overview/inspection, manual seed/size generation and benchmark staging. Their
programmatic event handlers also refuse to change an educational attempt.
Demo presentation controls and the original six benchmark scenarios remain.

## Questions, attempts and navigation

The read-only generated adapter now accepts `questionCount=4|5`, supplying it to
the **same source** Lite generator's `MAX_QUESTS`. No generator was rewritten.
Source SHA-256 remains
`03cd7fe5e60aec7d9cb47a799a8facfd73e4e3137602f5fd4edadb73b34ea564`.
Exact parity covers both counts, all four sizes and seeds 0, 1, 29, 20264049 and
4294967295. Approved five-question P0/P1 maps, seeds and benchmarks stay exact.

The shared attempt derives station IDs, question count, passed flags, HUD and
exit eligibility from the active assignment. Four-question units have no fifth
station. E retains P1's 70-pixel proximity, wall line-of-sight and absolute
virtual-speed ≤25 gates in both views. Opening an unanswered question does not
complete it. Returning without answering preserves state. A correct answer
marks exactly once, updates the relevant terminal texture/2D marker/HUD and
offers explanation text/video; it does **not** rebuild the maze mesh.

A wrong answer increments failures, clears all passes, keeps the unit and starts
a fresh random topology/vehicle with 30 seconds of map time. Size progression is
**25×19 → 21×15 → 17×13 → 13×9**, remaining 13×9 after later failures. Manual R
starts another random 25×19 maze for the same unit, zero failures and 30 seconds.
New units reset the same state. Resets clear held controls and stale dialogs.
Demo R retains its original same-seed behavior. The intended driving view is
preserved during resets.

All questions must pass to unlock EXIT. The student must then physically drive
there, stop and press E. Completion shows the unit/title, passed count, attempt
number and its validated Google Form URL. Question/explanation/Form anchors
use `target="_blank" rel="noopener noreferrer"`. There is no automatic playback,
Form submission, identity propagation, login, grade storage or progress saving.
External links are intercepted in tests; no actual service receives a submission.

V, M, arrow/WASD controls and zoom **125/150/175%** remain. The normal local 2D
view has no time limit. The full map retains one cumulative **30-second** budget,
settled against monotonic real time rather than the diagnostic physics clock.
Closing/reopening or changing views does not refill it. Inactive tabs, questions
and the unit selector pause consumption. Exhaustion leaves local 2D driving
available. Existing native-tab-focus and exhaustion tests are retained.

## Original 2D vehicle

`src/scene/vehicle2d.js` draws an original cyan/blue arcade car once into a
144×96 Canvas: gradient body, roof/rear window, pale windshield, four dark wheels,
pale front lamps, red rear lamps, bumpers, outline and shadow. There is no arrow
inside a decorative shell and no external asset/CDN. The car faces +X and rotates
by the authoritative +Y-down vehicle heading, matching 3D X/Z orientation.

Both map views use the same sprite centered on the projected vehicle position.
Local width is 46 CSS pixels; full-map width is 34. Existing camera projection,
collision dimensions and physics are unchanged. Amber/green question identities
and an above-car identity tag remain visible. The legend identifies the car.
Browser pixel checks verify front/rear colours at all four headings; actual
stationary steering, full routes, zoom/DPR/viewports exercise continuous rotation.

## Publication, packaging and hosting

Both committed Showcase manifests are **empty**. Synthetic v1/v2 test assignments
are copied only into disposable nested HTTP roots outside production `dist/`.
The GUI, schemas, original validators, Lite runtime and stable CI are unchanged.
Public JSON remains client-readable; this does not provide secure anti-cheating.

The instructor validates/exports approved units using the unchanged local GUI.
The same byte-identical Sxx files work in both editions. Explicitly copy approved
unit files into the intended package's **own** `dist/assignments/`, then manifest
**last**; remove unlisted public files. Keep drafts/backups outside the web root.
Optional Node development tools validate a publication or prepare it in a **new**
local folder, refusing overwrite. They never upload, synchronize or select units
for publication. Full commands and manual-only instructions are in
[the Showcase guide](../showcase3d/README.md#publish-assignments-explicitly--local-files-only).

Graphics builds preserve valid existing assignment bytes rather than deleting
`dist/`. The empty template initializes a new manifest only. Invalid/missing/
symlinked/unlisted publication files fail validation before runtime cleanup.
The packager includes verified build-listed runtime files, validated allowlisted
JSON and the five launcher/guide files. Arbitrary root files are excluded;
isolated tests prove exact publication preservation over two builds and ZIP
exclusion of a stray synthetic draft. Test/private folders never enter the ZIP.

**`test-results/3d-p2/showcase3d-p2-static.zip`** is the standalone delivery.
Extract completely and run **Start-Showcase.cmd**. Windows PowerShell 5.1/.NET
serves only dist over IPv4 loopback. No Node/npm/Python/Internet is required for
the scene or packaged local assignments. Optional Python stdlib serving remains.
YouTube/Forms need Internet; a browser-reported offline state displays a notice
and prevents external navigation while retaining the attempt. Internet loss
while a LAN remains connected may not change `navigator.onLine`.

For Apache, manually upload the dist contents to any chosen Showcase directory,
and approved units to that directory's `assignments/`, units first/manifest last.
Lite need not share the same path. Apache serves static files only. No backend,
secrets, automated deployment or automatic teacher-data upload is introduced.

## Automated validation

Required suite total is **236**: the 216 prior regressions plus 14 Node and six
P2 browser tests. Windows launcher checks are additional. Local/CI execution
details and the verified run are recorded below after verification.

| Suite | Coverage |
| --- | --- |
| Unchanged Lite, 151 | Python/schema/model, Tkinter/Xvfb, validation/student/gameplay/visual/browser suites; four CLI manifests |
| Showcase Node, 62 | Existing 48 plus validator identity/parity, both station counts/all sizes, answer and failure policy, loader races, publication preservation and ZIP privacy |
| Original Showcase Chromium, 12 | Existing keyboard route, 3D visual comparisons, presets/resources, context loss/recovery, benchmark and offline paths |
| P1.1 headed Chromium, 5 | Mixed-view full keyboard route, exact trajectories, resource stability, native tab focus, cumulative exhaustion, zoom/viewports and presentation recovery |
| P2 Chromium, 6 | Allowlist/error/refresh/cancel/stale/successful switches; earned-progress preservation; complete v1-four/v2-five keyboard routes; wrong then smaller complete challenge; all shrinking sizes; intercepted links; safe text/offline play; car four headings and viewports |
| Windows PowerShell 5.1 | Existing seven launcher HTTP/MIME/HEAD/dist-boundary checks |

Commands from the repository root:

```console
npm run build --prefix showcase3d
npm test --prefix showcase3d
xvfb-run -a python tests/run_ci.py
python showcase3d/tests/browser_showcase.py
xvfb-run -a -s "-screen 0 2048x1400x24 -nolisten tcp" python showcase3d/tests/browser_navigation.py
python showcase3d/tests/browser_education.py
python showcase3d/scripts/package.py
```

Codex uses its installed Chromium/video cache and separate virtual X displays.
Node/browser tests cannot silently skip. Browser fixtures are TEST ONLY; YouTube
and Form destinations are intercepted. Complete acceptance routes start at the
actual generated entry and use real W/S/A/D/V/M/E holds/clicks against unchanged
physics. Their diagnostic clock accelerates bounded physics intervals; it never
sets vehicle position or map allowance and is absent from normal URLs. Videos
are functional evidence, not real-time FPS measurements.

### GitHub Actions verification

Verification pending in this implementation checkpoint. Completion requires an
actual successful feature-branch run, all jobs and uploaded artifacts; YAML
validation alone is insufficient. The final report will replace this paragraph
with the verified run/source SHA and evidence links.

The feature workflow installs pinned development dependencies on Ubuntu 24.04,
Python 3.12/Node 24, Chromium and Xvfb, preserving Lite and Windows jobs. It runs
all original suites and P2 tests sequentially in the Showcase job, then packages
the static runtime. All evidence uploads even on failure with 14-day retention.
Token permission stays `contents: read`; checkout does not persist credentials.
No repository secrets or deployment are used.

## Evidence and performance

Full P2 evidence is under ignored **`test-results/3d-p2/`**: screenshots, console/
HTTP/request logs, traces, browser/state/results JSON, route plans and videos.
Original suites retain `3d-p1/` and `3d-p1.1/`. The two
`v1-four-complete-control-completion.json` /
`v2-five-complete-control-completion.json` files name their recordings in
`video/`, with accepted control plans and final states. Captures cover selection,
both views at one position, all headings, three/four-option questions, correct/
wrong feedback, smaller mazes, remaining full map, locked/unlocked exit and both
completion/Form dialogs. Selected safe PNGs are in **`docs/images/3d-p2/`**.

There are no new 3D per-frame meshes/materials or changed presets. Correct answers
only repaint existing screens and overlays; browser assertions require the same
rebuild counter. The cached car adds **55,296 backing bytes** (54 KiB). The JS
bundle grows from 604,028 to 624,033 bytes (+20,005, about 3.3% uncompressed),
including the actual shared validators and assignment UI.

The local retained resource test on the synthetic 13×9 map/Low/960×700/DPR 1
observed **23 geometries / 12 textures**, **2 rebuilds / 1 disposed scene**,
**1 static map cache build**, **119,808 cache bytes** and **1,854,720 visible
Canvas bytes**, unchanged across repeated view switching. Rolling Canvas CPU
paint mean was approximately **1.19 ms** at the final snapshot; it includes
JavaScript submission/startup work and is not GPU/compositor timing. These are
short Chromium 154/SwiftShader functional observations under shared cloud load,
not a sustained benchmark or Intel measurement. The original P0 comparison and
benchmark methodology remain intact.

## Instructor review and limitations

1. Extract/launch the default ZIP offline on Windows Chrome/Edge. Confirm demo
   and all original controls, quality presets, overview/inspection and benchmark.
2. In a separate local review package, manually add synthetic validated exports,
   units first/manifest last. Verify only listed units appear and refresh works.
   Repeat using the final nested Apache URL after manual upload.
3. Select v1-four and v2-five; cancel/failed-load from an in-progress attempt.
   Confirm position/progress/map time survive, and valid switching resets them.
4. Drive in 3D and 2D; verify cyan car/front/rear/turning, all zooms and arrow keys.
   Stop/E, close without answering, reopen, watch a question video and return.
   Choose one of multiple accepted v2 labels, then open its explanation.
5. Pass one question, then answer another incorrectly. Verify cleared progress,
   fresh 21×15 map, zero driving state and 30 seconds. Repeat to 17×13 and 13×9;
   R must restore 25×19/zero failures. Check all four/five markers and exit.
6. Spend M time over several openings, switch tabs, open the selector, and exhaust
   it. Local 2D remains usable; education exposes no unrestricted presentation
   controls. Answer all questions, drive to EXIT/E and open the correct Form.
7. Test offline local play, then reconnect for external services. Check 1280×800
   with Windows 150% display scaling, 1366×768 and 1920×1080 projector/fullscreen
   on UHD 770 and Arc 140V. Record actual device/browser/driver measurements.

P2 physical Windows educational gameplay and Arc 140V performance await review.
The instructor's approved smooth UHD 770 High appearance is qualitative;
numerical Intel FPS is unavailable. Linux Chromium/Xvfb and Windows HTTP launcher
tests do not verify physical Windows rendering, macOS or Safari. The Showcase
still requires WebGL 2 initialization, even for its added 2D view. Context loss
pauses play pending recovery. Progress is in memory and resets on reload.

Next action is instructor **P2 review**. No further phase has begun.

## Exact changed files

The final delivery lists paths relative to approved `7902de5` below. Generated
bundle names supersede the old P1.1 assets; Lite source/tests/stable workflow,
teacher tools, schemas, public Lite manifests and approved tags are unchanged.

Build/packaging changes preserve approved publications; source UI/model changes
implement the educational flow and car. The existing bundle-test helper now
enumerates the assignments directory; the keyboard planner accepts a checkpoint
count (its five-station default is unchanged). All new acceptance cases live in
separate P2 test files. Launchers change only their phase banner.

```text
M	.github/workflows/showcase3d.yml
M	AGENTS.md
M	Plan.md
M	README.md
M	showcase3d/README.md
D	showcase3d/dist/app-7TA3ZS5A.css
D	showcase3d/dist/app-J4CQ3FHR.js
M	showcase3d/dist/build-info.json
M	showcase3d/dist/index.html
M	showcase3d/index.html
M	showcase3d/launch.ps1
M	showcase3d/package-lock.json
M	showcase3d/package.json
M	showcase3d/scripts/build.mjs
M	showcase3d/scripts/export-maze.mjs
M	showcase3d/scripts/package.py
M	showcase3d/serve.py
M	showcase3d/src/gameplay/attempt.js
M	showcase3d/src/main.js
M	showcase3d/src/maze/generate.js
M	showcase3d/src/maze/lite-generated.js
M	showcase3d/src/scene/geometry.js
M	showcase3d/src/scene/map2d.js
M	showcase3d/src/style.css
M	showcase3d/tests/bundle.test.mjs
M	showcase3d/tests/control-route.mjs
A	docs/3d-p2-results.md
A	docs/images/3d-p2/car-heading-0.png
A	docs/images/3d-p2/correct-answer.png
A	docs/images/3d-p2/five-question-completion.png
A	docs/images/3d-p2/four-question-completion.png
A	docs/images/3d-p2/full-map-remaining.png
A	docs/images/3d-p2/published-unit-selector.png
A	docs/images/3d-p2/v1-four-options.png
A	docs/images/3d-p2/wrong-answer-smaller-maze.png
A	showcase3d/dist/app-4J526KQD.css
A	showcase3d/dist/app-Y2HAESKF.js
A	showcase3d/dist/assignments/manifest.json
A	showcase3d/public/assignments/manifest.json
A	showcase3d/scripts/check-publication.mjs
A	showcase3d/scripts/prepare-publication.mjs
A	showcase3d/scripts/publication.mjs
A	showcase3d/src/assignments/loader.js
A	showcase3d/src/assignments/question-ui.js
A	showcase3d/src/assignments/selector.js
A	showcase3d/src/assignments/validator.js
A	showcase3d/src/scene/vehicle2d.js
A	showcase3d/tests/browser_education.py
A	showcase3d/tests/education.test.mjs
A	showcase3d/tests/publication.test.mjs
A	showcase3d/tests/write-education-route.mjs
```
