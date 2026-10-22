# 3D-P0 — isolated Three.js laboratory maze

The instructor authorized this separate visual/GPU feasibility prototype on
2026-10-22. The reviewed Lite Phase 5B.1 baseline is
**`823786bc01b68901455061d5fe31d6076c61f20e`**, preserved by the new annotated,
pushed **`lite-v1.0`** tag. No previous tag existed; none was overwritten.
The baseline's GitHub Actions run
[39701908610](https://github.com/chingchechung/ece_hw_webproject/actions/runs/39701908610)
passed before development. Work continues only on **`feature/3d-showcase`**.
`work` and `main` are not merged or changed. **Stop after P0 for instructor
Windows hardware/visual review; do not start P1 educational integration.**

## Delivery and use

The new `showcase3d/` directory contains source, exact dependency lockfile,
read-only maze export/build scripts, a committed `dist/` runtime, offline
launchers, tests and attribution. Root README links the two editions and CI
artifacts; AGENTS/Plan record the explicitly authorized isolated track.
The original `student/`, tools, schemas, shared validators, original prototype,
assignments, 151 Lite tests and `.github/workflows/ci.yml` are byte-identical.
The preservation test checks SHA-256 hashes of **69** approved files.

For review, download the **showcase3d-p0-…** artifact from the successful feature
workflow, extract its **showcase3d-p0-static.zip** completely, then double-click
**Start-Showcase.cmd**. Windows PowerShell 5.1/.NET starts a loopback-only static
server and opens the default browser. No Node, npm, Python, build, Internet,
administrator privileges or public site is needed at the venue. The process-only
execution-policy setting does not change the computer's policy. Institutional
script restrictions may require an approved alternative; Python's optional
stdlib launcher is included. See [the presentation guide](../showcase3d/README.md).

Only `dist/` is served. Packaging uses an explicit allowlist, excluding teacher
drafts, private keys, student data, tests, dependencies and repository source.
Every marker is synthetic LAB 01–05; no assignment loader, answer validation,
YouTube, Forms, course unit or progress integration is present.

## Runtime and maze geometry

**Three.js 0.180.0**, `WebGLRenderer`, explicit **WebGL 2**, `PerspectiveCamera`,
ES modules; **esbuild 0.25.12** bundles the renderer and OrbitControls locally.
No CDN, WebGPU, backend, runtime fetch of remote assets or post-processing.
Node 24 is needed only for development. `npm ci && npm run build` reproduces the
committed hashed bundle. Tests compare every output byte against two fresh
builds; `build-info.json` records versions, hashes and Lite provenance without
timestamps or absolute build paths.

The build adapter reads the actual approved `randomizer`, `shuffle`,
`generateMaze` and `buildDriveRoad` functions from `student/js/game.js` without
editing them. An isolated Node VM injects a fixed clock/random input and a
five-marker count. It is a read-only deterministic export of the authoritative
generator, not a second algorithm or a copy of Lite gameplay. The extracted
generator SHA-256 is
`03cd7fe5e60aec7d9cb47a799a8facfd73e4e3137602f5fd4edadb73b34ea564`.
Tests fail if this reviewed source changes. Exported data has no course content.

| Logical size | Demonstration seed |
| --- | ---: |
| 25 × 19 | 20261022 |
| 21 × 15 | 20262031 |
| 17 × 13 | 20263040 |
| 13 × 9 | 20264049 |

The original widened driving mask is converted at **0.7 m per subcell**,
yielding 4.2 m corridors, at least 1.4 m separating wall cores, and 3.6 m wall
height. Full maze footprint is 70 × 53.2 m. Floors merge identical row-runs into
rectangles. Every exposed road/solid boundary becomes one collinear wall run;
solid top caps close the wall cores. The full map has 5,400 open subcells,
178 wall runs and 81 merged floor rectangles. Skirting, crown and safety trim
have distinct depths/heights. Contact shading is a shallow, vertex-gradient
multiply strip along actual wall edges. There are no pretend openings, painted
corridors or overlapping floor tiles. Tests enumerate every cell and boundary,
verify winding/finite world UVs, connectivity, genuine loops and T/four-way
junctions, and exercise movement against the same mask on all four sizes.

Static meshes and InstancedMesh batch panel joints, road stitches, ceiling
fixtures, terminal bodies/pedestals and exit posts. Five local instrument screens
and a clearly marked exit gantry provide representative engineering objects.
They are presentation objects without question interaction or prop collision.
Future P1 should define a reviewed read-only shared maze/state adapter and then
integrate shared gameplay incrementally; do not fork the generator or Lite physics.

## Materials, lighting and camera

All assets are original procedural content. No downloaded images, fonts, HDRs,
models or proprietary game artwork. The two MeshStandardMaterial PBR surfaces
use base color, tangent normal and packed AO/roughness/metalness maps. Walls have
composite/steel brushing, recessed gaskets, flush fasteners and darker lower
panels; epoxy/concrete floors have aggregate, broad surface variation and
expansion joints. UVs derive from world coordinates, independent of camera/frame
time. Physical panel joints and trim reinforce silhouettes without closing routes.
Texture mipmaps and bounded anisotropic filtering control distant detail.

A locally generated studio environment is filtered with PMREM. Hemisphere light
and one warm directional light keep routes readable; static baked contact strips
anchor walls. Medium/High optionally use one low-resolution static shadow map,
updated when a scene/preset changes. No per-terminal realtime lights, bloom,
screen-space reflections, expensive MSAA or horror darkness. First-person views
use restrained distance fog; overview disables it and hides the cutaway ceiling.
Attribution and the shipped Three.js MIT notice are in `THIRD_PARTY.md` and
`dist/LICENSES.txt`.

The isolated prototype controller uses W/S forward/reverse, A/D turning, mouse
drag look, and R/Reset. Eye height stays 1.65 m; swept substeps and a 0.25 m road
clearance prevent wall tunnelling. Blur/hiding clears movement. Overview's orbit
distance and polar angle keep the camera above walls/floor; panning is disabled.
This is not Lite's vehicle acceleration, turning model or 12× driving-distance
experience, and does not claim educational/gameplay parity.

## Presets, display scaling and diagnostics

| Setting | Low | Medium | High |
| --- | --- | --- | --- |
| Default scale | 0.70 | 0.85 | 1.00 |
| Maximum internal buffer | 1280 × 720 | 1600 × 900 | 1920 × 1080 |
| Each PBR texture | 128² | 256² | 512² |
| Anisotropy cap | 1 | 4 | 8 |
| Static directional shadow | None | 512² | 1024² |
| Default render cap | 30 FPS | 30 FPS | 30 FPS |
| Optional evaluation cap | 60 FPS | 60 FPS | 60 FPS |

Manual 0.5–1.25 scale overrides remain capped and preserve aspect ratio. Presets
never affect topology. `renderer.setPixelRatio(1)` deliberately avoids multiplying
buffers by Windows 150% scaling/DPR. Browser UI retains native CSS sizing. The
canvas excludes toolbar space, so a 1280×800 window does not imply a 1280×800
render buffer. Actual preset buffers and device DPR are shown and exported.
Automatic performance downscaling is deferred; manually choose Low/scale/cap.

The collapsible panel reports FPS, rendered-frame interval mean/p95, CPU render
submission time, internal size/DPR, GPU vendor/renderer where available, calls,
triangles, uploaded geometry/texture counts and approximate retained resource
budget. GPU execution uses asynchronous `EXT_disjoint_timer_query_webgl2` only
when available; disjoint results are discarded. Unsupported or unready timings
remain null/unavailable. CPU time is never relabelled GPU time. Pending queries
are bounded and cleared between samples/scenarios. GPU identity may be hidden by
the browser; it is diagnostic metadata, not proof of hardware throughput.

Memory estimates include six PBR mip chains (0.5 / 2 / 8 MiB), six synthetic
screen mip chains (~4 MiB), an approximate environment allowance (~4 MiB), shadow
depth (~0 / 1 / 4 MiB) and main color/depth buffers (~8 bytes/internal pixel).
They exclude driver/compositor overhead, geometry, garbage collection and
transient allocations; they are not measured dedicated VRAM. Uploaded resource
counts depend on visibility/shadow use. Repeated returns to the same preset
stabilize; replaced geometry, textures, materials, instance buffers and old shadow
targets are disposed. The Arc report's “16GB” is treated as shared-memory reporting.

## Automated results and Cloud evidence

The local suite passed **184 tests**: 151 unchanged Lite, 24 showcase Node, and
9 showcase browser tests (zero failures/skips). The final camera/metadata build
is being rechecked; feature GitHub Actions verification will be recorded after
its first push. The unchanged Lite runner already passed **151**
tests with zero failures/skips, including schema/model, Tkinter/Xvfb, v1/v2
browser validation/loading, Phase 4 complete gameplay, and all approved Phase 5
artwork/input regressions. All four assignment CLI checks passed.

Commands used (from repository root unless noted):

```console
# showcase3d directory
npm ci
npm run build
npm test
# repository root, with Xvfb display available
python tests/run_ci.py
python showcase3d/tests/browser_showcase.py
python showcase3d/scripts/package.py
python showcase3d/serve.py --no-browser --port 8788
```

The 24 isolated Node tests cover source provenance/determinism, 69-file Lite
preservation, every floor cell/wall edge on all four maps, valid geometry/UVs,
collision/loops/junctions, bounded buffers, statistical summaries, relative local
resources, launcher/package boundaries and two-build reproducibility.
The separate browser suite checks WebGL 2, nested relative paths, blocked external
network requests, all sizes/presets/resource disposal, single-preset stability,
keyboard/mouse/reset/orbit, 1280×800 at DPR 1.5, projector resizing to 1920×1080,
fullscreen, context loss/restoration, unavailable-WebGL fallback, all six benchmark
scenarios, local JSON download, deterministic screenshots and real navigation.
Any uncaught JavaScript error, console error or external request fails the suite.
There is no unexpected page scrolling.

Local browser: Chromium **154.0.8037.57** (actual version JSON in artifacts),
Playwright **1.62.0**, Python **3.12.14**, Linux Cloud. WebGL initialized as
**WebGL 2.0 (OpenGL ES 3.0 Chromium)** through
**ANGLE / Vulkan SwiftShader Device (Subzero)**. This is **software rendering**.
It is a functional/visual check and is slow, not an Intel performance result.
Shortened automated benchmark captures warm for 400 ms and sample 1.2 s; they
exercise the recording/export path and are not suitable for hardware acceptance.
Cold navigation/module/scene/shader preparation and first submission are exported
separately from warmed frame statistics. Shader preparation is elapsed setup time,
not fabricated GPU timing. Cold metadata explicitly labels the initial Medium
preset/map/buffer; later preset switches are warmed scenario measurements.
`KHR_parallel_shader_compile` may be unavailable in
Cloud; the explicit warning is retained in logs.

Feature-only `.github/workflows/showcase3d.yml` runs separate Ubuntu showcase and
unchanged Lite jobs, plus a Windows PowerShell 5.1 launcher HTTP smoke job. It has
read-only contents permissions, no secrets and no deployment. Pushes that affect
showcase/CI or protected Lite code trigger it; root documentation-only updates do
not rerun it. The stable work workflow remains unchanged. Synthetic screenshots,
traces, console/failure logs, browser/Node results, benchmark JSON, real-browser
video and standalone ZIP upload even on failure, with 14-day artifact retention.
Windows launcher CI tests local HTTP/MIME/HEAD and rejects private/outside paths;
it does not measure either physical Intel GPU or establish native browser parity.

## Visual evidence

The final screenshots and recording are actual Chromium/WebGL rendering, not
mockups or generated evidence. Few representative PNGs are committed under
`docs/images/3d-p0/`; the full gallery stays in ignored artifacts:

- `straight.png`, `t-junction.png`, `four-way.png`, `wall.png`, `floor.png`.
- `checkpoint.png`, `finish.png`, `start.png` (first-person).
- `full-maze-overview.png`, `showcase-composition.png`.
- `matched-low.png`, `matched-medium.png`, `matched-high.png`, at the same seed,
  camera and window, with matching diagnostic JSON.
- `projector-1920x1080.png` and per-test screenshots/traces/logs.
- `navigation-evidence.json` names the dedicated `video/*.webm` recording:
  actual W/A keyboard movement, turning into a junction, changing view distances
  and switching presets. Cloud footage is explicitly not a hardware FPS demo.
- `cloud-benchmark.json`, `browser-results.json`, `browser-version.json`,
  `node-tests.log`, `browser-tests.log`, `showcase3d-p0-static.zip`.

## Windows benchmark procedure — same test on both physical devices

No actual Intel frame-rate result has been obtained in this development session.
The following specifications were supplied by the instructor, not remeasured:

| Target | Supplied hardware/browser | Review status |
| --- | --- | --- |
| A / minimum | Windows 11, Chrome 155, Intel UHD 770, driver 30.0.101.1002, ANGLE/D3D11, DX12.1, ~31 GiB RAM, 20 logical CPUs, 60 Hz, reported 1812×1019 / scale 1.06 | Pending physical review |
| B / presentation | Windows 11, Chrome 155, Intel Arc 140V, driver 32.0.101.8132, ANGLE/D3D11, DX12.2, ~31 GiB RAM, 8 logical CPUs, 60 Hz, 1280×800 / scale 1.5 | Pending physical review |

Both reports indicate accelerated WebGL/WebGPU; this prototype uses WebGL 2 only.
The Arc shared-memory “16GB” report is not a dedicated-VRAM guarantee. The NPU is
unused. Avoid high-sample MSAA defaults on both Intel devices.

1. Extract the same static package on both machines. Plug the laptop into power;
   record power mode, driver, Chrome/Edge version, browser zoom, display/scaling,
   external-monitor connection and other heavy applications. Keep those fixed.
2. Launch locally with Internet disconnected. Verify no missing textures/scripts,
   the panel says WebGL 2 and reports the expected Intel/ANGLE renderer rather
   than SwiftShader. If acceleration is unavailable, fix the browser/driver first.
3. On **UHD 770**, begin Low / 30 FPS. Use an approximately 1280×720 *internal*
   buffer where viewport/caps permit; check actual panel resolution. Record it
   rather than assuming the window size is the internal buffer. Stable 30 FPS
   at this approximate buffer is a target, not a passed claim.
4. On **Arc 140V**, begin Medium / 30 FPS in a 1280×800 layout at Windows 150%
   scaling, browser zoom 100%. Verify readable controls, no scrolling and a
   bounded internal buffer. Repeat High / 30 FPS, then evaluate Low/Medium / 60
   FPS. High at 60 FPS is explicitly unverified.
5. Reload once for the initial **Medium** cold measurement, then choose the
   desired preset/cap/resolution and set the device label. Run the six-scene benchmark: full maze overview,
   smallest maze overview, straight corridor, four-way junction, terminal and
   deterministic motion/right-angle turns. Default: 1 s warm-up + 5 s sampling
   per scene. Repeat at least **three warmed runs** per setting. Export JSON
   after each run before changing settings. Keep all six scenarios/seeds equal.
6. Compare frame mean/p95, FPS, GPU timings only if available, resolution and
   CPU submission time. Note intermittent stutters, thermal/power behavior,
   visual aliasing and time to first frame. A capped 30 FPS run should approach
   33.3 ms cadence; a 60 FPS goal approaches 16.7 ms. These reference intervals
   are evaluation criteria, not guarantees or automatic pass/fail assertions.
7. Repeat the laptop test with the 1920×1080 external projector, both windowed
   and fullscreen. Record whether it is mirrored/extended and the browser's
   effective CSS viewport/DPR. Repeat live preset switches, all maze sizes,
   Reset/R and first-person/overview. Confirm labels at presentation distance.
8. Run a 10-minute presentation rehearsal, revisit the same preset/map, and
   export another report to inspect resource counts and sustained behavior.
   If the context is lost, verify recovery or the clear reload instruction.
   Record crashes/errors or any view that crosses a wall/floor.
9. Return the exported JSON files, representative screenshots, device settings
   and subjective readability/visual feedback for P0 review. The app itself
   never uploads them. Repeat the controls/offline smoke in Edge separately;
   Chrome results alone do not establish Edge or Safari compatibility.

Simple instructor checklist (complete once per physical computer):

- [ ] Package starts offline through the one-click launcher; close/restart works.
- [ ] Correct Intel/ANGLE renderer; device label/version/driver recorded.
- [ ] W/A/S/D, mouse look, Reset/R, all four maps, terminal/exit inspection work.
- [ ] No wall/floor clipping, false openings, flickering surfaces or unreadable routes.
- [ ] Low/Medium/High switches preserve topology; resolution override stays bounded.
- [ ] Six-scene JSON exported for cold + three warm runs at agreed settings.
- [ ] Laptop 150% scaling, fullscreen and 1080p projector remain readable/no-scroll.
- [ ] Sustained rehearsal and context-recovery/reload behavior recorded.
- [ ] Visual quality, FPS/p95 evidence and any failures returned for review.

## Limits and next phase

Real Windows GPU performance and native Chrome/Edge presentation behavior are
pending instructor tests. macOS/Safari are untested; optional future WebKit CI
would be a separate functional check, not a Safari compatibility claim. Cloud
SwiftShader video/frame rates do not support hardware performance promises.
Native Windows launcher HTTP checks are separated from GPU testing.
No automatic quality adaptation, full physics, course interactions or gameplay
parity is provided. Synthetic props do not block movement. High-quality shadow
coverage is intentionally economical and may need tuning on physical GPUs.

Next is **P0 instructor review**, then an explicitly authorized **3D-P1** sharing
design for maze data, input/physics and assignment/UI state. Prerequisites for
that integration include accepted visuals and actual UHD 770 / Arc 140V results.
Do not begin P1 or merge to `work`/`main` before approval.

## Exact changed files


Root guidance/entry documentation records isolation; the new feature workflow
adds showcase/Lite preservation/Windows launcher jobs. All renderer, adapter,
materials, diagnostics, offline packaging, source tests and committed runtime
files are new under `showcase3d/`. This report and three real-browser PNGs provide
review evidence. Exact paths:

```text
.github/workflows/showcase3d.yml
AGENTS.md
Plan.md
README.md
docs/3d-p0-results.md
docs/images/3d-p0/full-maze-overview.png
docs/images/3d-p0/junction-high.png
docs/images/3d-p0/laboratory-terminal.png
showcase3d/.gitignore
showcase3d/README.md
showcase3d/Start-Showcase.cmd
showcase3d/THIRD_PARTY.md
showcase3d/dist/LICENSES.txt
showcase3d/dist/app-4JUWX4SJ.js
showcase3d/dist/app-RD2YC7DH.css
showcase3d/dist/build-info.json
showcase3d/dist/index.html
showcase3d/index.html
showcase3d/launch.ps1
showcase3d/package-lock.json
showcase3d/package.json
showcase3d/scripts/build.mjs
showcase3d/scripts/export-maze.mjs
showcase3d/scripts/package.py
showcase3d/serve.py
showcase3d/src/camera/controller.js
showcase3d/src/main.js
showcase3d/src/materials/laboratory.js
showcase3d/src/maze/layout.js
showcase3d/src/maze/maps.json
showcase3d/src/performance/metrics.js
showcase3d/src/performance/quality.js
showcase3d/src/scene/geometry.js
showcase3d/src/style.css
showcase3d/tests/browser_showcase.py
showcase3d/tests/bundle.test.mjs
showcase3d/tests/geometry.test.mjs
showcase3d/tests/launcher-smoke.ps1
showcase3d/tests/lite-baseline.json
```
