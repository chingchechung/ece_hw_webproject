# Engineering Maze Lab — 3D Showcase P0

A separate visual feasibility prototype. No real questions, answers, course
files, submission links, student records or saved progress. Lite is unchanged.
**Stop at P0 for review; this controller does not implement Lite driving physics.**

## Present offline on Windows 11

1. Download the **showcase3d-p0-…** artifact from the latest successful
   **3D showcase P0** GitHub Actions run on `feature/3d-showcase`.
2. Extract `showcase3d-p0-static.zip` completely to a local folder. Alternatively,
   download the feature branch and use its complete `showcase3d/` folder.
3. Double-click **Start-Showcase.cmd**. The built-in Windows PowerShell/.NET
   launcher opens `http://127.0.0.1:8787/` in the default browser (or the next
   free port through 8797). Use Chrome/Edge with graphics acceleration enabled.
4. Keep the launcher window open; close it or press Ctrl+C when finished.

No Internet, npm, Node, Python, admin privileges, public hosting or rebuild is
needed at the venue. Do not double-click `dist/index.html`; ES modules require
local HTTP. The launcher binds IPv4 loopback and serves **dist only**, never
teacher drafts or the repository. It uses a process-only PowerShell execution
policy override, without changing the machine policy. If organizational policy
blocks scripts, use the optional Python launcher below or ask local IT for an
approved local-static-server method. Native Windows launcher execution remains
part of instructor hardware review; Linux testing does not verify PowerShell.

Optional cross-platform launcher, Python 3.12 stdlib only:

```console
python showcase3d/serve.py
# From inside a standalone extracted package:
python serve.py
```

## Controls and review

W/S move; A/D turn; mouse drag looks; R or Reset returns to the seeded start.
Focus the scene before keyboard navigation. Movement stops on blur/hiding.
Overview enables a bounded orbit above the walls; dragging rotates, wheel zooms.
The Inspect menu stages repeatable real corridor/junction/terminal/exit views.
The synthetic instruments and exit have no gameplay or collision interaction.
Fullscreen uses the browser API; F11 is the Windows alternative.

Start UHD 770 review at **Low**, 30 FPS. Start Arc 140V at **Medium**, 30 FPS.
Low/Medium/High use 0.70/0.85/1.00 render scales, bounded by
1280×720 / 1600×900 / 1920×1080. These apply to the canvas, excluding toolbar
space; actual internal height therefore varies. Manual resolution overrides are
still bounded by each preset. Render DPR is deliberately 1 even at Windows 150%
scaling; controls retain browser CSS sizing. No MSAA or post-processing.
60 FPS is an evaluation setting, not a promised result.

The diagnostics panel reports rendered-frame interval mean/p95, FPS, CPU render
submission time, optional asynchronous GPU timer measurements, draw/triangle/
resource counts and estimated memory. Estimates are not measured VRAM. Timer
queries may be unavailable, delayed or invalidated; null means unavailable.
Do not compare Cloud SwiftShader frame rates with Intel hardware results.

Run the six-scene benchmark with the same preset, cap, window and resolution on
both machines. Each scenario warms for 1 second and records 5 seconds; repeat
after a cold page load and at least three times warm. Cold loading/shader times
are separate fields. Choose the correct device label and **Export local JSON**.
The exported file stays on the computer; no data is uploaded or stored by the app.
Cancel preserves completed scenarios and marks the run incomplete in the UI.
See [the complete two-device procedure](../docs/3d-p0-results.md) in the repository.

## Development / reproducible bundle

Node 24, Python 3.12 for tests. From `showcase3d/`:

```console
npm ci
npm run build
npm test
```

`three` **0.180.0**, `esbuild` **0.25.12**, exact lockfile. `dist/` is committed
and venue-ready; do not edit it by hand. The build uses no timestamps, CDN or
absolute paths. Tests compare its bytes with two fresh builds. The read-only
adapter executes the reviewed Lite maze generator with deterministic clock/random
inputs and records its source hash, seed, topology hash and baseline SHA. It does
not import course data or change Lite source. `src/maze/maps.json` contains only
the four synthetic demonstration layouts. Future P1 sharing needs a reviewed
read-only maze-data boundary, not an independent authoritative generator.

From the repository root:

```console
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python showcase3d/tests/browser_showcase.py
python showcase3d/scripts/package.py
```

The separate browser suite forces Chromium SwiftShader for repeatable **Cloud
functional checks**. It uses the installed Playwright Chromium, falling back to a
system Chromium in Codex Cloud; `EMI_3D_BROWSER_PATH` overrides the executable.
Its browser, server, synthetic fixtures and Node dependencies are outside `dist/`.
Outputs live only under ignored `test-results/3d-p0/`. `window.showcase.snapshot()`
and `runBenchmark({warmupMs,durationMs})` are local diagnostic interfaces; shortened
automated captures are functional checks, not the recommended hardware benchmark.

`python showcase3d/scripts/package.py` creates the allowlisted standalone ZIP in
`test-results/3d-p0/`. The feature-only CI runs these checks and the unchanged
151-test Lite suite in separate jobs. The stable `work` workflow is byte-identical.

## Scope and limits

Windows/Intel and native PowerShell require instructor verification. No macOS/
Safari compatibility claim. No shared gameplay, automatic quality adaptation,
cockpit, reflections post-process, physics engine or course integrations. The
context-loss handler requests browser recovery and shows a reload instruction
if recovery fails. Reload/reset are always available through browser controls.
