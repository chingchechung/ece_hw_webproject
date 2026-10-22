import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import './style.css';
import data from './maze/maps.json' with { type: 'json' };
import { CELL, center, viewPose, walkable, move, DIRECTIONS } from './maze/layout.js';
import { buildMazeScene } from './scene/geometry.js';
import { createMaterials, studioEnvironment } from './materials/laboratory.js';
import { Controller } from './camera/controller.js';
import { PRESETS, resolution } from './performance/quality.js';
import { Metrics } from './performance/metrics.js';
import { generateMap } from './maze/generate.js';
import { stepDriving, canDriveStand } from './gameplay/driving.js';
import { createAttempt, pauseAttempt, nearestInteraction, interact } from './gameplay/attempt.js';
import { virtualSpeedToMeters } from './gameplay/coordinates.js';

const $ = id => document.getElementById(id);
const cold = { moduleReadyMs: performance.now() };
let renderer, metrics, scene, camera, environment, controller, orbit, model, surfaces, sun;
let current = data.maps[0], quality = 'Medium', override = null, mode = 'first-person';
let attempt = createAttempt(current), view = 'driving';
const testClock = new URL(location.href).searchParams.get('testClock') === '1';
let ready = false, contextLost = false, lastFrame = 0, lastRender = 0, lastPanel = 0, buffer = {};
let benchmark = null, benchmarkResults = [], rebuilds = 0, disposedScenes = 0, restoredContexts = 0;
const labels = { start: 'Laboratory corridor', straight: 'Materials / long corridor', 't-junction': 'Three-way laboratory junction',
  'four-way': 'Four-way engineering junction', checkpoint: 'Signal analysis terminal', finish: 'Demonstration exit',
  wall: 'Composite / brushed steel', floor: 'Epoxy / concrete finish' };

function message(text, error = false) { $('message').textContent = text; $('message').classList.toggle('error', error); }
function resize() {
  if (!renderer) return;
  const { width, height } = $('stage').getBoundingClientRect();
  buffer = resolution(Math.max(1, width), Math.max(1, height), quality, override);
  renderer.setSize(buffer.width, buffer.height, false);
  camera.aspect = width / height; camera.updateProjectionMatrix();
}
function inspect(type) {
  scene.fog = new THREE.Fog('#83969b', 28, 85);
  pauseGame(); view = 'inspection'; document.body.dataset.view = view; mode = 'first-person'; controller.enabled = true; controller.driving = false; orbit.enabled = false;
  model.ceilings.visible = true; $('camera').textContent = 'Return to driving'; $('inspection').value = type;
  controller.pose = viewPose(current, type === 'wall' || type === 'floor' ? 'straight' : type);
  if (type === 'wall') {
    const p = controller.pose; p.yaw += Math.PI / 2; p.pitch = -0.05; move(current, p, 0.7);
    const x = p.x - Math.sin(p.yaw), z = p.z + Math.cos(p.yaw);
    if (walkable(current, x, z)) { p.x = x; p.z = z; }
    p.yaw += 0.14;
  }
  if (type === 'floor') controller.pose.pitch = -0.6;
  controller.apply(camera); $('scene-name').textContent = labels[type]; metrics.reset();
  $('view').focus({ preventScroll: true });
}
function overview() {
  pauseGame(); view = 'overview'; document.body.dataset.view = view; mode = 'overview'; controller.enabled = false; orbit.enabled = true; model.ceilings.visible = false;
  scene.fog = null;
  const w = current.driveRoad.w * CELL, h = current.driveRoad.h * CELL;
  orbit.target.set(w / 2, 0, h / 2); camera.position.set(w * 1.04, Math.max(w, h) * 0.95, h * 1.25);
  orbit.minDistance = Math.max(12, w * 0.35); orbit.maxDistance = Math.max(w, h) * 2;
  orbit.maxPolarAngle = Math.PI * 0.32; orbit.minPolarAngle = 0.12;
  orbit.enablePan = false; orbit.update(); $('camera').textContent = 'Return to driving';
  $('scene-name').textContent = 'Maze architecture / full overview'; metrics.reset();
}
function configureLighting() {
  const shadow = PRESETS[quality].shadow;
  renderer.shadowMap.enabled = Boolean(shadow); renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.shadowMap.autoUpdate = false; renderer.shadowMap.needsUpdate = true;
  sun.castShadow = Boolean(shadow);
  if (sun.shadow.map) { sun.shadow.map.dispose(); sun.shadow.map = null; }
  sun.shadow.mapSize.set(shadow || 256, shadow || 256);
  const w = current.driveRoad.w * CELL, h = current.driveRoad.h * CELL;
  sun.position.set(w / 2 + 12, 35, h / 2 - 8); sun.target.position.set(w / 2, 0, h / 2);
  Object.assign(sun.shadow.camera, { left: -w * 0.75, right: w * 0.75, top: h * 0.75, bottom: -h * 0.75, near: 1, far: 100 });
  sun.shadow.camera.updateProjectionMatrix(); sun.shadow.bias = -0.0003; sun.shadow.normalBias = 0.035;
}
function rebuild() {
  if (model) { model.dispose(); disposedScenes++; }
  if (!surfaces) surfaces = createMaterials(PRESETS[quality], renderer.capabilities.getMaxAnisotropy());
  model = buildMazeScene(current, surfaces.materials); scene.add(model.group); rebuilds++;
  configureLighting();
  if (mode === 'overview') model.ceilings.visible = false;
  renderer.renderLists.dispose(); metrics.reset(); resize();
  $('seed-label').textContent = `${current.width} × ${current.height} · seed ${current.seed} · topology ${current.topologyHash.slice(0, 14)}`;
  refreshHud();
}
function setQuality(next) {
  if (!PRESETS[next] || contextLost || benchmarkRunning) return;
  quality = next;
  document.querySelectorAll('[data-quality]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.quality === quality)));
  const previous = surfaces;
  surfaces = createMaterials(PRESETS[quality], renderer.capabilities.getMaxAnisotropy());
  model.setMaterials(surfaces.materials); previous.dispose();
  configureLighting(); metrics.reset(); resize(); refreshHud();
  $('view').focus({ preventScroll: true });
}
function canDrive() { return ready && view === 'driving' && !attempt.interaction && !attempt.finished && !benchmarkRunning && !contextLost && !document.hidden; }
function pauseGame() { controller?.clear(); pauseAttempt(attempt); }
function resumeDriving() {
  pauseGame(); view = 'driving'; mode = 'first-person'; document.body.dataset.view = view;
  scene.fog = new THREE.Fog('#83969b',28,85); orbit.enabled = false; controller.enabled = true; controller.driving = true;
  model.ceilings.visible = true; controller.follow(attempt.vehicle,camera);
  $('camera').textContent = 'Overview'; $('inspection').value = 'driving';
  $('scene-name').textContent = 'Maze driving / five laboratories';
  metrics.reset(); refreshHud(); $('view').focus({ preventScroll: true });
}
function resetAttempt() {
  if (benchmarkRunning) return;
  pauseGame(); attempt = createAttempt(current); controller.pitch = 0;
  $('dialog-overlay').hidden = true; resumeDriving();
  $('status').textContent = 'Attempt reset · same seed · five synthetic labs';
}
function mazeChanged(map) { return map.seed !== current.seed || map.topologyHash !== current.topologyHash || map.id !== current.id; }
function replaceMap(map) {
  pauseGame(); $('dialog-overlay').hidden = true;
  const changed = mazeChanged(map);
  current = map; attempt = createAttempt(current); controller.pitch = 0;
  if (changed) rebuild();
  resumeDriving();
}
function generate() {
  if (benchmarkRunning || contextLost) return;
  const text = $('seed').value.trim();
  if (text && (!/^\d+$/.test(text) || !Number.isSafeInteger(Number(text)) || Number(text)>4294967295)) {
    $('status').textContent = 'Enter a seed from 0 to 4294967295, or leave it blank for random.';
    $('maze').value = current.id; return;
  }
  let seed = text ? Number(text) : crypto.getRandomValues(new Uint32Array(1))[0];
  if (!text && seed === current.seed) seed = (seed+1)>>>0;
  const [w,h] = $('maze').value.split('x').map(Number);
  replaceMap(generateMap(w,h,seed));
  $('status').textContent = `New maze · seed ${seed} · synthetic demonstration`;
}
function text(id,value) { const node = $(id); if (node.textContent !== value) node.textContent = value; }
function refreshHud() {
  if (!model) return;
  const near = nearestInteraction(current,attempt), count = attempt.completed.filter(Boolean).length;
  text('speed',String(Math.round(Math.abs(attempt.vehicle.speed)*.25)) + (attempt.vehicle.speed<0 ? ' R' : ''));
  text('progress',`${count} / 5`);
  text('nearby',attempt.finished ? 'Demonstration complete' : near ? `${near.id} · ${near.label}` : count===5 ? 'Exit unlocked' : 'Find Q1–Q5');
  const active = view==='driving' && !benchmarkRunning;
  text('interaction-hint',!active ? 'Paused · return to driving to activate' : near ? Math.abs(attempt.vehicle.speed)>25 ? 'Brake to activate · speed must be ≤25 virtual' : near.type==='finish' && count<5 ? 'Exit locked · complete all five labs' : 'Press E to activate' : 'W accelerate · S brake / reverse · A/D steer');
  $('interact').hidden = !active || !near || !!attempt.interaction || attempt.finished;
  model.updateProgress(attempt.completed,active ? near : null,benchmarkRunning);
  text('control-hint',testClock ? 'Test clock active · keyboard drives the real physics' : active ? 'W accelerate · S brake/reverse · A/D steer · E activate' : 'Inspection paused · drag to look · return to driving');
}
function activate() {
  if (!canDrive()) return;
  const result = interact(current,attempt);
  if (result.status==='outside') return;
  if (result.status==='moving') { $('status').textContent = 'Brake and stop near the marker before pressing E.'; $('view').focus({preventScroll:true}); return; }
  if (result.status==='locked') { $('status').textContent = 'Exit locked: activate all five synthetic checkpoints first.'; $('view').focus({preventScroll:true}); return; }
  if (result.status!=='activated') return;
  controller.clear(); refreshHud();
  $('dialog-title').textContent = result.type==='finish' ? 'Demonstration complete' : `${result.id} · ${result.label} — Checkpoint Activated`;
  $('dialog-text').textContent = result.type==='finish' ? 'All five labs are activated. You reached the exit using the maze driving controller. No grades, student data or submission are recorded.' : 'Synthetic laboratory checkpoint activated. Continue driving to the remaining labs, then reach the unlocked exit. No course question is loaded.';
  $('dialog-overlay').hidden = false; $('dialog-close').focus();
}
function closeDialog() {
  if ($('dialog-overlay').hidden) return;
  attempt.interaction = null; $('dialog-overlay').hidden = true; controller.clear(); refreshHud(); $('view').focus({ preventScroll:true });
}
function physicsTick(dt,input) { if (canDrive()) attempt.vehicle = stepDriving(current,attempt.vehicle,input,dt); }
function advanceSimulation(seconds) {
  if (!testClock || !Number.isFinite(seconds) || seconds<0 || seconds>20) throw new Error('Only the explicit local test clock may advance 0–20 seconds');
  const input = controller.input();
  for (let remaining=seconds;remaining>1e-10;) { const dt=Math.min(1/60,remaining); physicsTick(dt,input); remaining-=dt; }
  if (view==='driving') controller.follow(attempt.vehicle,camera);
  refreshHud(); return snapshot();
}
function snapshot() {
  if (!renderer) return { ready: false, webgl2: false };
  const stats = renderer.info, preset = PRESETS[quality];
  // Estimates cover owned texture mip chains and main color/depth buffers, not browser/driver overhead.
  const estimatedResources = { pbrTextureBytes: surfaces.estimatedTextureBytes,
    screenTextureBytes: 6 * 512 * 256 * 4 * 4 / 3,
    environmentApproxBytes: 2 * 1024 * 256 * 8,
    shadowApproxBytes: preset.shadow ** 2 * 4,
    framebufferApproxBytes: buffer.width * buffer.height * 8,
    note: 'Budget estimate, not measured VRAM. Excludes driver, compositor, geometry and transient allocations; shared GPU memory is not dedicated VRAM.' };
  return { phase: '3D-P1', ready, webgl2: renderer.capabilities.isWebGL2, three: THREE.REVISION,
    baseline: data.baseline, generatorHash: data.generatorHash, quality, scaleOverride: override,
    targetFps: Number($('fps').value), buffer, devicePixelRatio: window.devicePixelRatio, rendererPixelRatio: renderer.getPixelRatio(),
    viewport: { width: innerWidth, height: innerHeight }, mode, view, testClock, game: JSON.parse(JSON.stringify(attempt)), heldKeys: [...controller.keys], metersPerSecond: virtualSpeedToMeters(attempt.vehicle.speed), vehicleClear: canDriveStand(current,attempt.vehicle.x,attempt.vehicle.y), pose: { ...controller.pose },
    camera: camera.position.toArray(), cameraWalkable: mode === 'overview' || walkable(current, camera.position.x, camera.position.z),
    maze: { id: current.id, seed: current.seed, topologyHash: current.topologyHash, ...model.stats },
    render: { calls: stats.render.calls, triangles: stats.render.triangles, geometries: stats.memory.geometries, textures: stats.memory.textures },
    estimatedResources, metrics: metrics.snapshot(), coldStart: { ...cold }, rebuilds, disposedScenes, restoredContexts, contextLost,
    benchmark: benchmark && { scenario: benchmark.name, running: true },
    benchmarkResults: [...benchmarkResults], selectedDevice: $('device').value, userAgent: navigator.userAgent };
}
const display = n => n == null ? 'unavailable' : n.toFixed(1);
function updatePanel() {
  const s = snapshot(), m = s.metrics, total = Object.values(s.estimatedResources).filter(v => typeof v === 'number').reduce((a, b) => a + b, 0);
  $('fps-badge').textContent = `${display(m.fps)} FPS`;
  $('stats').textContent = `${quality} · ${$('fps').value} FPS cap\n${buffer.width} × ${buffer.height} internal\nDPR ${devicePixelRatio} · render DPR 1\nFrame interval mean / p95\n  ${display(m.frameIntervalMs.mean)} / ${display(m.frameIntervalMs.p95)} ms\nCPU render submission\n  ${display(m.cpuSubmissionMs.mean)} ms mean\nGPU execution\n  ${display(m.gpuExecutionMs.mean)} ms mean\n${s.render.calls} draws · ${s.render.triangles.toLocaleString()} tris\n${s.render.geometries} geometries · ${s.render.textures} textures\n~${(total / 1048576).toFixed(1)} MiB estimated resources\n${m.identity.renderer}\n${m.identity.vendor}\n${m.identity.classification}`;
}
function exportResults() {
  const report = snapshot(); delete report.game; delete report.heldKeys;
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob), a = document.createElement('a');
  a.href = url; a.download = `emi-3dp1-${quality.toLowerCase()}-${Date.now()}.json`; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function routeFor(map) {
  const target = map.stations[0], queue = [{ x: 1, y: 1 }], previous = new Map([['1,1', null]]);
  for (let i = 0; i < queue.length; i++) {
    const p = queue[i]; if (p.x === target.x && p.y === target.y) break;
    DIRECTIONS.forEach(([dx, dy]) => {
      const x = p.x + dx, y = p.y + dy, key = `${x},${y}`;
      if (y > 0 && y < map.height - 1 && x > 0 && x < map.width - 1 && map.grid[y * 2][x * 2] === 0 && !previous.has(key)) {
        previous.set(key, p); queue.push({ x, y });
      }
    });
  }
  const result = []; let p = target;
  while (p) { result.unshift(center(p)); p = previous.get(`${p.x},${p.y}`); }
  return result;
}
let route = [];
function benchmarkPose(progress) {
  if (!benchmark?.motion || route.length < 2) return;
  const t = Math.min(0.999, progress) * Math.min(route.length - 1, 12), index = Math.floor(t), a = route[index], b = route[index + 1];
  controller.pose = { x: a.x + (b.x - a.x) * (t - index), z: a.z + (b.z - a.z) * (t - index),
    yaw: Math.atan2(b.z - a.z, b.x - a.x), pitch: 0 };
  controller.apply(camera);
}
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
let cancelBenchmark = false, benchmarkRunning = false;
async function runBenchmark({ warmupMs = 1000, durationMs = 5000 } = {}) {
  if (!ready || benchmarkRunning || contextLost || attempt.interaction) return;
  warmupMs = Math.max(200, Math.min(10000, warmupMs)); durationMs = Math.max(600, Math.min(60000, durationMs));
  pauseGame();
  const saved = { current, attempt, view, inspection: $('inspection').value, pose: { ...controller.pose } };
  benchmarkRunning = true; cancelBenchmark = false; benchmarkResults = [];
  $('benchmark').disabled = true; $('cancel-benchmark').hidden = false;
  for (const el of document.querySelectorAll('nav button, nav select, nav input, #inspection')) el.disabled = true;
  const scenarios = [ ['Full-size maze', 0, 'overview'], ['Smallest maze', 3, 'overview'],
    ['Straight corridor', 0, 'straight'], ['Complex intersection', 0, 'four-way'],
    ['Checkpoint area', 0, 'checkpoint'], ['Motion / right-angle turns', 0, 'start'] ];
  try {
    for (const [name, index, view] of scenarios) {
      if (cancelBenchmark || contextLost) break;
      const changed = mazeChanged(data.maps[index]);
      current = data.maps[index]; attempt = createAttempt(current); $('maze').value = current.id;
      if (changed) rebuild();
      if (view === 'overview') overview(); else inspect(view);
      route = routeFor(current); controller.enabled = false;
      benchmark = { name, motion: name.startsWith('Motion'), start: performance.now() + warmupMs, durationMs };
      $('status').textContent = `Benchmark: ${name} · warm-up ${warmupMs} ms + capture ${durationMs} ms`;
      await wait(warmupMs); metrics.reset();
      await wait(durationMs);
      if (cancelBenchmark || contextLost) break;
      const result = snapshot(); delete result.benchmarkResults; delete result.game; delete result.heldKeys;
      benchmarkResults.push({ scenario: name, warmupMs, durationMs, report: result });
    }
  } finally {
    const changed = mazeChanged(saved.current);
    benchmark = null; benchmarkRunning = false; current = saved.current; attempt = saved.attempt; $('maze').value = current.id;
    if (changed) rebuild();
    if (saved.view==='overview') overview(); else if (saved.view==='inspection') { inspect(saved.inspection); controller.pose = saved.pose; controller.apply(camera); } else resumeDriving();
    $('benchmark').disabled = false; $('cancel-benchmark').hidden = true;
    for (const el of document.querySelectorAll('nav button, nav select, nav input, #inspection')) el.disabled = false;
    $('status').textContent = `Benchmark ${cancelBenchmark || contextLost ? 'interrupted' : 'complete'} · ${benchmarkResults.length}/6 scenes · export JSON locally`;
  }
  return [...benchmarkResults];
}
function frame(now) {
  requestAnimationFrame(frame);
  if (!ready || contextLost || document.hidden) { lastFrame = now; return; }
  const dt = Math.min(0.045, Math.max(0, (now - lastFrame) / 1000)); lastFrame = now;
  if (!benchmarkRunning) {
    if (view==='driving') { if (!testClock) physicsTick(dt,controller.input()); controller.follow(attempt.vehicle,camera); }
    else if (mode==='overview') orbit.update(); else controller.apply(camera);
    refreshHud();
  }
  else benchmarkPose(Math.max(0, (now - benchmark.start) / benchmark.durationMs));
  const interval = 1000 / Number($('fps').value);
  if (now - lastRender < interval - 1) return;
  lastRender = now - ((now - lastRender) % interval);
  metrics.begin(now); renderer.render(scene, camera); metrics.end();
  if (!cold.firstFrameSubmittedMs) cold.firstFrameSubmittedMs = performance.now();
  if (now - lastPanel > 750) { updatePanel(); lastPanel = now; }
}
async function initialize() {
  const canvas = $('view'), gl = canvas.getContext('webgl2', { antialias: false, alpha: false, powerPreference: 'high-performance' });
  if (!gl) throw new Error('WebGL 2 could not start. Enable browser graphics acceleration, update the graphics driver, and restart Chrome or Edge. This separate P1 showcase requires WebGL 2; use the Lite edition if unavailable.');
  renderer = new THREE.WebGLRenderer({ canvas, context: gl, antialias: false, alpha: false });
  renderer.setPixelRatio(1); renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.12;
  scene = new THREE.Scene(); scene.background = new THREE.Color('#344752');
  scene.fog = new THREE.Fog('#83969b', 28, 85);
  camera = new THREE.PerspectiveCamera(68, 1, 0.08, 220);
  environment = studioEnvironment(renderer); scene.environment = environment.texture;
  scene.add(new THREE.HemisphereLight('#e8f4f2', '#4c626b', 2.35));
  sun = new THREE.DirectionalLight('#fff1d8', 2.1); scene.add(sun, sun.target);
  metrics = new Metrics(renderer); controller = new Controller(canvas, { reset: resetAttempt, pause: pauseGame, close: closeDialog, interact: activate, canDrive });
  orbit = new OrbitControls(camera, canvas); orbit.enabled = false; orbit.enableDamping = true;
  rebuild(); resumeDriving(); cold.sceneBuiltMs = performance.now();
  cold.initialPreset = quality; cold.initialMaze = current.id; cold.initialBuffer = { ...buffer };
  const prep = performance.now(); await renderer.compileAsync(scene, camera);
  cold.shaderPreparationMs = performance.now() - prep; cold.readyMs = performance.now();
  ready = true; message('');
  canvas.addEventListener('webglcontextlost', event => {
    event.preventDefault(); contextLost = true; pauseGame(); cancelBenchmark = true;
    metrics.pending = []; // Context-owned query handles are invalid after loss.
    message('Graphics context lost. Waiting for the browser to restore it. If this persists, reload the local page.');
  });
  canvas.addEventListener('webglcontextrestored', async () => {
    try {
      metrics.dispose(); metrics = new Metrics(renderer);
      // Render-target contents cannot be re-uploaded from CPU images after loss.
      environment.dispose(); environment = studioEnvironment(renderer); scene.environment = environment.texture;
      if (sun.shadow.map) { sun.shadow.map.dispose(); sun.shadow.map = null; }
      renderer.shadowMap.needsUpdate = true;
      await renderer.compileAsync(scene, camera);
      contextLost = false; restoredContexts++; resize(); message('');
    } catch { message('Graphics recovery failed. Reload the local page to restart.', true); }
  });
  $('maze').addEventListener('change',generate); $('generate').addEventListener('click',generate);
  document.querySelectorAll('[data-quality]').forEach(button => button.addEventListener('click', () => setQuality(button.dataset.quality)));
  $('scale').addEventListener('change', () => { override = $('scale').value === 'auto' ? null : Number($('scale').value); resize(); metrics.reset(); });
  $('fps').addEventListener('change', () => metrics.reset());
  $('inspection').addEventListener('change', () => $('inspection').value==='driving' ? resumeDriving() : inspect($('inspection').value));
  $('reset').addEventListener('click', resetAttempt);
  $('interact').addEventListener('click',activate); $('dialog-close').addEventListener('click',closeDialog);
  $('camera').addEventListener('click', () => view==='driving' ? overview() : resumeDriving());
  $('fullscreen').addEventListener('click', async () => {
    try { if (document.fullscreenElement) await document.exitFullscreen(); else await document.documentElement.requestFullscreen(); }
    catch { $('status').textContent = 'Fullscreen unavailable. Use the browser fullscreen command (F11 on Windows).'; }
    $('view').focus({preventScroll:true});
  });
  $('benchmark').addEventListener('click', () => runBenchmark());
  $('cancel-benchmark').addEventListener('click', () => { cancelBenchmark = true; });
  $('export').addEventListener('click', exportResults);
  new ResizeObserver(resize).observe($('stage')); window.addEventListener('resize', resize);
  document.addEventListener('visibilitychange', () => { metrics.reset(); lastFrame = performance.now(); });
  window.showcase = Object.freeze({ snapshot, runBenchmark, ...(testClock ? { advanceSimulation } : {}) });
  window.addEventListener('pagehide', () => { cancelBenchmark = true; metrics.dispose(); model.dispose(); surfaces.dispose(); environment.dispose(); orbit.dispose(); renderer.dispose(); });
  requestAnimationFrame(frame);
}
initialize().catch(error => {
  message(error.message || 'The local 3D scene could not initialize. Reload or use the Lite edition.', true);
  $('status').textContent = '3D unavailable · no course data has been loaded';
  document.querySelectorAll('button, select').forEach(el => { el.disabled = true; });
});
