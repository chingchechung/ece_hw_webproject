# Engineering Maze Lab — Educational Assignments P2

The approved dual-view driving and P0 Three.js/WebGL 2 artwork now support
**Educational Assignment Mode** alongside **3D Demonstration Mode**. The release
contains an empty public manifest: no course questions, instructor drafts or
student information. Educational play uses the same published v1/v2 JSON as Lite.
Physical P1.1 navigation is approved. Stop after P2 for instructor review;
no numerical Intel performance result was supplied.

## Start offline on Windows 11

1. In GitHub **Actions → 3D showcase P2**, open the successful feature-branch
   run and download **showcase3d-p2-…**.
2. Under `3d-p2/`, extract **showcase3d-p2-static.zip** completely to a local folder.
3. Double-click **Start-Showcase.cmd**. Built-in Windows PowerShell 5.1/.NET
   starts a server at `http://127.0.0.1:8787/` (next free port through 8797) and
   opens the default browser. Use Chrome or Edge with graphics acceleration.
4. Keep the launcher window open. Close it or press Ctrl+C to stop.

No Node, npm, Python, rebuilding, administrator privileges or public hosting is
required at the venue. The scene and demo work offline. Locally packaged
assignments work offline; YouTube and Google Forms require Internet. The offline
notice explains this and prevents external links when the browser reports offline.
Serve the complete committed `dist/` directory
for static hosting. Do not open `index.html` using `file://`.

The launcher binds IPv4 loopback and serves **dist only**, never repository
source or teacher drafts. Its execution-policy override is process-only.
Institutional script policy may require an approved alternative. Optional
cross-platform launcher with Python 3.12 stdlib: `python serve.py` from the
extracted package, or `python showcase3d/serve.py` from the repository root.
Windows-runner HTTP checks do not verify the physical presentation computer.

## Choose an educational assignment

**Educational Assignment Mode** pauses driving and opens the public unit selector.
Only S01–S12 explicitly listed in the validated local
`./assignments/manifest.json` appear. **Refresh manifest** rereads it without
cache. An empty manifest clearly reports that no units have been published.
Earlier published units remain playable for review; the game does not manage
Google Forms availability. Missing or invalid JSON never launches a challenge
or substitutes demo questions.

Choose a unit, then confirm the new attempt. The application fetches and validates
its declared Sxx file before changing modes. Cancel, failed loading and stale
responses preserve the existing position, progress and remaining map time.
The selector pauses map consumption. A successful load starts a fresh 25×19
maze, zero failures, cleared answers and 30 seconds of map allowance.
**3D Demonstration Mode** explicitly returns to the separate synthetic LAB mode
after confirmation. It uses no official questions or Form.

Both v1 (four options, `correctOption`) and v2 (three/four options,
`correctOptions`) use the actual unchanged Lite validators. A student clicks
**one** A/B/C/D option; any accepted label passes. Four-question units have
exactly four checkpoints; five-question units have five. No conversion is needed.

Drive near an incomplete Q01–Q04/Q05, stop, and press **E** in either view.
The dialog shows unit/question text, English question video and actual answer
choices. Closing without answering preserves the attempt. Video links open
separate tabs; background driving stops. Correct answers turn the checkpoint
green and offer explanation text/video. All questions must pass before the exit
unlocks. Physically drive there, stop and press E to see the unit's Google Form
link and attempt number. The game never submits, records grades or asks for IDs.

A wrong answer clears every passed flag, keeps the unit, creates a new random
maze and restores the map budget. Sizes shrink **25×19 → 21×15 → 17×13 → 13×9**;
later failures stay 13×9. **Reset / R** starts a fresh random 25×19 attempt for
that unit with zero failures and 30 seconds. It keeps the chosen driving view.
Unlimited overview, inspection, manual seed/size generation and benchmarks are
hidden/guarded during educational play, so they cannot bypass the map allowance.

## Publish assignments explicitly — local files only

The Python GUI is unchanged. Validate/export only units the instructor has
explicitly approved, together with their allowlist manifest, to a separate local
export directory outside the web root. The identical Sxx files work in Lite
and Showcase; there is no 3D schema or automatic migration.

For an extracted offline package, manually copy those approved Sxx files into
`showcase3d/dist/assignments/`, then copy **manifest.json last**. Replace the empty
manifest intentionally. Remove any old unit files no longer listed; keep their
private copies outside the package. Never copy a draft/export parent directory
or all S01–S12 indiscriminately. Keep private drafts, backups and student data
outside `dist/` and artifact folders. No development tools are needed to play.

Optional development checks/helpers, from the repository root with Node 24:

```console
node showcase3d/scripts/check-publication.mjs /path/to/already-published/assignments
node showcase3d/scripts/prepare-publication.mjs /path/to/already-published/assignments /path/to/NEW-local-assignments
```

The helper validates all data before copying exact original bytes, units first
and manifest last. It refuses an existing destination; choose a new folder and
manually place its files into the desired package. It does not choose units,
alter content, upload or synchronize anything. The checker/build/package refuse
invalid, missing, symlinked or unlisted assignment files. A graphics rebuild
preserves existing valid `dist/assignments/` bytes. The empty
`public/assignments/manifest.json` initializes only a new publication directory;
it does not overwrite a valid instructor manifest. Do not commit private course
exports or run CI against them: the repository release stays empty.

For Apache, manually upload the runtime files inside `dist/` into the chosen
Showcase directory, and approved JSON into **that directory's own**
`assignments/`. Upload Sxx files first and manifest last. Lite may live elsewhere;
the loader never assumes their paths match. No Node, Python, PHP, API or database
runs on Apache. Test the final nested URL, refresh the manifest, select each
published unit, and verify an unlisted unit is absent. Static JSON exposes its
answers to browser users; this is not secure anti-cheating.

## Drive and activate the demonstration labs

- Click the scene to focus it. **W** accelerates, **S** brakes and then reverses,
  **A/D** steer (including stationary steering); arrow keys are aliases.
- Mouse drag adjusts vertical look while driving. Heading follows steering;
  horizontal mouse look is available in inspection views. No passive camera
  bob, shaking or motion blur is added.
- Approach **Q1–Q5 / LAB 01–05**, reduce speed, then press **E** or the activation
  button. Range is 70 Lite world pixels (3.5 m) around the authoritative station
  centre; the screen/pedestal sits 1.25 m toward a wall. Walls block activation.
- Activation requires virtual speed ≤25 in either direction (about 6 on the
  virtual km/h display). E at higher speed only shows a braking reminder.
- E activates a synthetic checkpoint once and opens an acknowledgement dialog.
  Continue driving after closing it. Completed screens turn green and progress
  increases. A held/repeated E does not reactivate completed labs.
- All five labs unlock the exit. Drive there, stop and press **E** to finish.
  The completion screen records no submission or personal data. Close it, then
  use Reset/R or Generate for another drive.

In demo mode, **Reset / R** restarts the current seed and clears speed, steering, keys,
progress, dialogs and full-map allowance. It keeps your chosen driving view.
**Generate** uses an optional uint32 seed (0–4294967295),
or a new random seed if blank. Select any original maze size. Reset keeps the
same map; Generate/size selection explicitly starts a fresh attempt, including
30 seconds of map allowance. Invalid seeds preserve the current attempt.
Seed 0 follows Lite's existing fallback to RNG seed 29.

## Dual-view navigation

**V / 2D driving / 3D driving** changes presentation. Both views use the very
same vehicle, `stepDriving()` function, maze, checkpoint flags and exit. Switching
stops speed and releases held controls, preserving exact position, heading,
distance, seed and progress. The controls above work in either view. The 2D
car rotates with the vehicle heading, including continuous steering. Its original
cached Canvas artwork has four wheels, cyan body/roof, windows, pale headlights
and red rear lamps. The same centered car appears in the full map.

The player-centered Canvas 2D view shows real roads and walls. Amber circles are
incomplete Q1–Q5; green boxes/checks are completed labs. EXIT shows LOCKED or OPEN.
**2D zoom 125% / 150% / 175%** changes a uniform scale; 150% is the default.
The local scale adapts to viewport/map size and always crops the map. The camera
follows the player and clamps at maze boundaries. No click-to-move, route planner,
target arrow or separate walking physics is present.

**M / Full map** opens/closes a different, complete maze map. Driving pauses.
The countdown is **30 seconds cumulative per attempt**, not per opening. Closing
pauses it. A background/hidden or unfocused tab does not consume time; returning
continues the same remaining allowance. WebGL context loss pauses counting too.
Question dialogs and unit selection also pause consumption. At zero it closes
and cannot reopen until a new attempt (reset, wrong answer or valid unit load;
Generate in demo).
Ordinary local 2D driving still works. The diagnostic simulation clock never
fast-forwards this real wall-clock allowance. Escape also closes the full map.

V closes an open full map, then changes the driving view without restoring time.
V/M do not dismiss checkpoint dialogs; close the dialog or reset first. Typing
in the seed field or selecting an option does not trigger shortcuts.

In demo mode, **3D presentation overview** is the existing unlimited developer/presentation
camera, clearly separate from the timed gameplay map. It pauses driving and
keeps position/progress. Drag/wheel inspects the whole architecture; **Return to
driving** resumes the intended 2D or 3D view at the same vehicle position with zero
speed. Inspect views stage only the camera and also preserve the vehicle. V/M
operate only in driving views. Mouse
look never changes vehicle heading. Blur/hiding and dialogs stop the vehicle and
release controls. The wall collision model is Lite's; synthetic props remain
non-colliding presentation objects.

## Quality and measurement

P0 PBR materials, lighting, world UVs and Low/Medium/High definitions remain.
Scales are 0.70 / 0.85 / 1.00, bounded by 1280×720 / 1600×900 / 1920×1080;
manual overrides remain capped. Render DPR is deliberately 1 at Windows 150%
scaling. The UI retains browser CSS sizing. No MSAA, post-processing or CDN.
Default cap is 30 FPS; 60 FPS is an evaluation setting. Quality changes replace
material maps and shadow targets, without rebuilding maze geometry or progress.

The collapsible panel reports frame mean/p95, FPS, CPU submission, optional GPU
timer queries, draw/triangle/resource counts and estimated memory. Null GPU time
means unavailable; CPU time is not GPU time, and estimates are not measured VRAM.

The six-scene benchmark retains the P0 seeds/routes: full maze, smallest maze,
straight corridor, intersection, terminal, motion/turning. Each warms for 1 s and
samples for 5 s. It pauses and restores the current attempt; cold setup is labelled
separately as initial Medium. Choose a device label, repeat at least three warm
runs, and **Export local JSON** after each. No data is uploaded.

The instructor qualitatively approved P0 High on a physical UHD 770 as very
smooth with excellent visuals. **No numerical Intel GPU benchmark has been
provided.** P1 driving was subsequently approved after physical testing.
P1.1 navigation is approved; P2 and Arc 140V presentation review remain pending. Cloud SwiftShader performance
is software rendering, not Intel throughput.

Before a presentation, verify offline launch, steering/braking/reverse, all five
labs and exit, reset/new seeds, mode returns, live quality changes, 1280×800 at
150% scaling, fullscreen and the 1080p projector. Export measurements from both
physical devices. See `docs/3d-p1-results.md` in the repository for the complete
hardware review procedure, parity evidence and limitations. Navigation-specific
results are in `docs/3d-p1.1-results.md`; educational/publication review steps and
P2 evidence are in `docs/3d-p2-results.md`.

## Development and tests

Pinned Three.js **0.180.0**, esbuild **0.25.12**; Node 24 and exact lockfile:

```console
cd showcase3d
npm ci
npm run build
npm test
```

`dist/` is committed and reproducible. Never edit generated output manually.
The read-only build adapter exports the approved fixed maps and generates
`src/maze/lite-generated.js` directly from the immutable Lite generator. Browser
runtime uses ordinary static JavaScript, with no eval, VM, source fetching or
second author-maintained maze algorithm. Runtime layouts use a labelled FNV
fingerprint for diagnostics; the original P0 benchmark maps retain SHA-256 IDs.

All authoritative physics positions remain Lite world pixels; centralized helpers
convert 14 pixels to 0.7 m only at the rendering boundary. Pure driving equations
match the actual Lite functions frame by frame, including the .045 s frame cap,
12× virtual distance, nine-point 6-pixel clearance and collision sliding.

From the repository root:

```console
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python showcase3d/tests/browser_showcase.py
python showcase3d/tests/browser_navigation.py
python showcase3d/tests/browser_education.py
python showcase3d/scripts/package.py
```

The navigation suite uses a windowed Chromium instance to test actual tab focus.
On a headless Linux machine, run it under a virtual display instead:

```console
xvfb-run -a -s "-screen 0 2048x1400x24 -nolisten tcp" python showcase3d/tests/browser_navigation.py
```

Test fixtures and infrastructure stay outside `dist/`. The frozen approved P0
source baseline builds only under ignored `test-results/3d-p1/p0-runtime/` for
paired real-browser image comparisons. The accepted end-to-end test starts at the
actual entry and uses real keyboard holds for a complete five-lab/exit route.
`?testClock=1` explicitly enables a diagnostic simulation clock; only that mode
exposes `window.showcase.advanceSimulation(seconds)` (bounded to 20 s per call).
It advances the actual physics using held keyboard input and never sets positions.
Its accelerated-clock video is functional evidence, not a real-time FPS benchmark.
Normal presentation URLs use real animation-frame timing and expose no clock hook.
The separate navigation suite retains evidence in `test-results/3d-p1.1/`, including
a complete real-keyboard 3D → 2D → Q1 → 3D → exit recording, actual cumulative timer
exhaustion, emulated hidden events and actual tab focus loss/return. The original
P1 browser suite and all Lite tests remain unchanged.

The separate feature CI runs all Lite regressions, Node source/physics/geometry
checks, Chromium/WebGL driving, navigation and educational checks, and Windows
launcher checks. P2 fixtures are served only from disposable nested test roots;
no test assignments enter production `dist/`. The P2 suite records complete
four-question v1 and five-question v2 keyboard routes, intercepted external links,
wrong-answer size progression, selector safety, car headings and viewports.
Synthetic logs, screenshots, traces, videos, JSON and the static ZIP upload even
on failure. The stable `work` workflow and Lite implementation remain unchanged.
Artifacts are retained 14 days. macOS/Safari remain untested.
