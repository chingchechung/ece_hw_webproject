# Engineering Maze Lab — 3D Driving P1

Five **synthetic** laboratory checkpoints, the approved Lite arcade driving
model, and the approved P0 Three.js/WebGL 2 artwork. No real course questions,
answer keys, Forms, student records, grades or saved progress. Stop at P1 for
instructor driving review before any P2 educational integration.

## Start offline on Windows 11

1. In GitHub **Actions → 3D showcase P1**, open the successful feature-branch
   run and download **showcase3d-p1-…**.
2. Extract its **showcase3d-p1-static.zip** completely to a local folder.
3. Double-click **Start-Showcase.cmd**. Built-in Windows PowerShell 5.1/.NET
   starts a server at `http://127.0.0.1:8787/` (next free port through 8797) and
   opens the default browser. Use Chrome or Edge with graphics acceleration.
4. Keep the launcher window open. Close it or press Ctrl+C to stop.

No Node, npm, Python, rebuilding, Internet, administrator privileges or public
hosting is required at the venue. Serve the complete committed `dist/` directory
for static hosting. Do not open `index.html` using `file://`.

The launcher binds IPv4 loopback and serves **dist only**, never repository
source or teacher drafts. Its execution-policy override is process-only.
Institutional script policy may require an approved alternative. Optional
cross-platform launcher with Python 3.12 stdlib: `python serve.py` from the
extracted package, or `python showcase3d/serve.py` from the repository root.
Windows-runner HTTP checks do not verify the physical presentation computer.

## Drive and activate the labs

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
  The completion screen records no submission or personal data.

**Reset / R** restarts the current seed and clears speed, steering, keys,
progress and dialogs. **Generate** uses an optional uint32 seed (0–4294967295),
or a new random seed if blank. Select any original maze size. Reset keeps the
same map; Generate/size selection clears the attempt. Invalid seeds preserve the
current attempt. Seed 0 follows Lite's existing fallback to RNG seed 29.

**Overview** pauses driving and keeps position/progress. Drag/wheel inspects the
whole maze; **Return to driving** resumes at the same vehicle position with zero
speed. Inspect views stage only the camera and also preserve the vehicle. Mouse
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
provided.** P1 driving on UHD 770 and Arc 140V still needs physical review.
Cloud SwiftShader performance is software rendering, not Intel throughput.

Before a presentation, verify offline launch, steering/braking/reverse, all five
labs and exit, reset/new seeds, mode returns, live quality changes, 1280×800 at
150% scaling, fullscreen and the 1080p projector. Export measurements from both
physical devices. See `docs/3d-p1-results.md` in the repository for the complete
hardware review procedure, parity evidence and limitations.

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
python showcase3d/scripts/package.py
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

The separate feature CI runs all Lite regressions, Node source/physics/geometry
checks, Chromium/WebGL driving and visual checks, and Windows launcher checks.
Synthetic logs, screenshots, traces, videos, JSON and the static ZIP upload even
on failure. The stable `work` workflow and Lite implementation remain unchanged.
Artifacts are retained 14 days. macOS/Safari remain untested.
