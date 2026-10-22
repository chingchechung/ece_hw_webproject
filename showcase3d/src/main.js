import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import './style.css';
import data from './maze/maps.json';
import { CELL, center, viewPose, walkable, move, DIRECTIONS } from './maze/layout.js';
import { buildMazeScene } from './scene/geometry.js';
import { createMaterials, studioEnvironment } from './materials/laboratory.js';
import { Controller } from './camera/controller.js';
import { PRESETS, resolution } from './performance/quality.js';
import { Metrics } from './performance/metrics.js';

const $ = id => document.getElementById(id);
const cold = { moduleReadyMs: performance.now() };
let renderer, metrics, scene, camera, environment, controller, orbit, model, surfaces, sun;
let current = data.maps[0], quality = 'Medium', override = null, mode = 'first-person';
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
  controller.clear(); mode = 'first-person'; controller.enabled = true; orbit.enabled = false;
  model.ceilings.visible = true; $('camera').textContent = 'Overview'; $('inspection').value = type;
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
  mode = 'overview'; controller.enabled = false; controller.clear(); orbit.enabled = true; model.ceilings.visible = false;
  scene.fog = null;
  const w = current.driveRoad.w * CELL, h = current.driveRoad.h * CELL;
  orbit.target.set(w / 2, 0, h / 2); camera.position.set(w * 1.04, Math.max(w, h) * 0.95, h * 1.25);
  orbit.minDistance = Math.max(12, w * 0.35); orbit.maxDistance = Math.max(w, h) * 2;
  orbit.maxPolarAngle = Math.PI * 0.32; orbit.minPolarAngle = 0.12;
  orbit.enablePan = false; orbit.update(); $('camera').textContent = 'First-person';
  $('scene-name').textContent = 'Maze architecture / full overview'; metrics.reset();
}
function rebuild() {
  if (model) { model.dispose(); disposedScenes++; }
  if (surfaces) surfaces.dispose();
  surfaces = createMaterials(PRESETS[quality], renderer.capabilities.getMaxAnisotropy());
  model = buildMazeScene(current, surfaces.materials); scene.add(model.group); rebuilds++;
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
  if (mode === 'overview') model.ceilings.visible = false;
  renderer.renderLists.dispose(); metrics.reset(); resize();
  $('seed-label').textContent = `${current.width} × ${current.height} · seed ${current.seed} · topology ${current.topologyHash.slice(0, 10)}`;
}
function setQuality(next) {
  if (!PRESETS[next] || contextLost) return;
  quality = next;
  document.querySelectorAll('[data-quality]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.quality === quality)));
  rebuild();
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
  return { phase: '3D-P0', ready, webgl2: renderer.capabilities.isWebGL2, three: THREE.REVISION,
    baseline: data.baseline, generatorHash: data.generatorHash, quality, scaleOverride: override,
    targetFps: Number($('fps').value), buffer, devicePixelRatio: window.devicePixelRatio, rendererPixelRatio: renderer.getPixelRatio(),
    viewport: { width: innerWidth, height: innerHeight }, mode, pose: { ...controller.pose },
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
  const blob = new Blob([JSON.stringify(snapshot(), null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob), a = document.createElement('a');
  a.href = url; a.download = `emi-3dp0-${quality.toLowerCase()}-${Date.now()}.json`; a.click();
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
  if (!ready || benchmarkRunning || contextLost) return;
  warmupMs = Math.max(200, Math.min(10000, warmupMs)); durationMs = Math.max(600, Math.min(60000, durationMs));
  benchmarkRunning = true; cancelBenchmark = false; benchmarkResults = [];
  $('benchmark').disabled = true; $('cancel-benchmark').hidden = false;
  for (const el of document.querySelectorAll('nav button, nav select, #inspection, #view')) el.disabled = true;
  const scenarios = [ ['Full-size maze', 0, 'overview'], ['Smallest maze', 3, 'overview'],
    ['Straight corridor', 0, 'straight'], ['Complex intersection', 0, 'four-way'],
    ['Checkpoint area', 0, 'checkpoint'], ['Motion / right-angle turns', 0, 'start'] ];
  try {
    for (const [name, index, view] of scenarios) {
      if (cancelBenchmark || contextLost) break;
      current = data.maps[index]; $('maze').value = current.id; rebuild();
      if (view === 'overview') overview(); else inspect(view);
      route = routeFor(current); controller.enabled = false;
      benchmark = { name, motion: name.startsWith('Motion'), start: performance.now() + warmupMs, durationMs };
      $('status').textContent = `Benchmark: ${name} · warm-up ${warmupMs} ms + capture ${durationMs} ms`;
      await wait(warmupMs); metrics.reset();
      await wait(durationMs);
      if (cancelBenchmark || contextLost) break;
      const result = snapshot(); delete result.benchmarkResults;
      benchmarkResults.push({ scenario: name, warmupMs, durationMs, report: result });
    }
  } finally {
    benchmark = null; benchmarkRunning = false; controller.enabled = mode === 'first-person';
    $('benchmark').disabled = false; $('cancel-benchmark').hidden = true;
    for (const el of document.querySelectorAll('nav button, nav select, #inspection')) el.disabled = false;
    $('status').textContent = `Benchmark ${cancelBenchmark || contextLost ? 'interrupted' : 'complete'} · ${benchmarkResults.length}/6 scenes · export JSON locally`;
  }
  return [...benchmarkResults];
}
function frame(now) {
  requestAnimationFrame(frame);
  if (!ready || contextLost || document.hidden) { lastFrame = now; return; }
  const dt = Math.min(0.05, Math.max(0, (now - lastFrame) / 1000)); lastFrame = now;
  if (!benchmarkRunning) { controller.update(current, dt, camera); if (mode === 'overview') orbit.update(); }
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
  if (!gl) throw new Error('WebGL 2 could not start. Enable browser graphics acceleration, update the graphics driver, and restart Chrome or Edge. This separate P0 prototype requires WebGL 2; use the Lite edition if unavailable.');
  renderer = new THREE.WebGLRenderer({ canvas, context: gl, antialias: false, alpha: false });
  renderer.setPixelRatio(1); renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.12;
  scene = new THREE.Scene(); scene.background = new THREE.Color('#344752');
  scene.fog = new THREE.Fog('#83969b', 28, 85);
  camera = new THREE.PerspectiveCamera(68, 1, 0.08, 220);
  environment = studioEnvironment(renderer); scene.environment = environment.texture;
  scene.add(new THREE.HemisphereLight('#e8f4f2', '#4c626b', 2.35));
  sun = new THREE.DirectionalLight('#fff1d8', 2.1); scene.add(sun, sun.target);
  metrics = new Metrics(renderer); controller = new Controller(canvas, () => inspect('start'));
  orbit = new OrbitControls(camera, canvas); orbit.enabled = false; orbit.enableDamping = true;
  rebuild(); inspect('start'); cold.sceneBuiltMs = performance.now();
  cold.initialPreset = quality; cold.initialMaze = current.id; cold.initialBuffer = { ...buffer };
  const prep = performance.now(); await renderer.compileAsync(scene, camera);
  cold.shaderPreparationMs = performance.now() - prep; cold.readyMs = performance.now();
  ready = true; message('');
  canvas.addEventListener('webglcontextlost', event => {
    event.preventDefault(); contextLost = true; controller.clear(); cancelBenchmark = true;
    metrics.pending = []; // Context-owned query handles are invalid after loss.
    message('Graphics context lost. Waiting for the browser to restore it. If this persists, reload the local page.');
  });
  canvas.addEventListener('webglcontextrestored', async () => {
    try {
      metrics.dispose(); metrics = new Metrics(renderer); await renderer.compileAsync(scene, camera);
      contextLost = false; restoredContexts++; resize(); message('');
    } catch { message('Graphics recovery failed. Reload the local page to restart.', true); }
  });
  $('maze').addEventListener('change', () => { current = data.maps.find(map => map.id === $('maze').value); rebuild(); inspect('start'); });
  document.querySelectorAll('[data-quality]').forEach(button => button.addEventListener('click', () => setQuality(button.dataset.quality)));
  $('scale').addEventListener('change', () => { override = $('scale').value === 'auto' ? null : Number($('scale').value); resize(); metrics.reset(); });
  $('fps').addEventListener('change', () => metrics.reset());
  $('inspection').addEventListener('change', () => inspect($('inspection').value));
  $('reset').addEventListener('click', () => inspect('start'));
  $('camera').addEventListener('click', () => mode === 'first-person' ? overview() : inspect('start'));
  $('fullscreen').addEventListener('click', async () => {
    try { if (document.fullscreenElement) await document.exitFullscreen(); else await document.documentElement.requestFullscreen(); }
    catch { $('status').textContent = 'Fullscreen unavailable. Use the browser fullscreen command (F11 on Windows).'; }
  });
  $('benchmark').addEventListener('click', () => runBenchmark());
  $('cancel-benchmark').addEventListener('click', () => { cancelBenchmark = true; });
  $('export').addEventListener('click', exportResults);
  new ResizeObserver(resize).observe($('stage')); window.addEventListener('resize', resize);
  document.addEventListener('visibilitychange', () => { metrics.reset(); lastFrame = performance.now(); });
  window.showcase = Object.freeze({ snapshot, runBenchmark });
  window.addEventListener('pagehide', () => { cancelBenchmark = true; metrics.dispose(); model.dispose(); surfaces.dispose(); environment.dispose(); orbit.dispose(); renderer.dispose(); });
  requestAnimationFrame(frame);
}
initialize().catch(error => {
  message(error.message || 'The local 3D scene could not initialize. Reload or use the Lite edition.', true);
  $('status').textContent = '3D unavailable · no course data has been loaded';
  document.querySelectorAll('button, select').forEach(el => { el.disabled = true; });
});
