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
import { createAttempt, pauseAttempt, nearestInteraction, interact, answerQuestion, attemptSize } from './gameplay/attempt.js';
import { virtualSpeedToMeters } from './gameplay/coordinates.js';
import { consumeMapAllowance, setMapOpen } from './gameplay/navigation.js';
import { Map2D } from './scene/map2d.js';
import { AssignmentSelector } from './assignments/selector.js';
import { questionContents, correctContents, finishContents } from './assignments/question-ui.js';

const $ = id => document.getElementById(id);
const cold = { moduleReadyMs: performance.now() };
let renderer, metrics, scene, camera, environment, controller, orbit, model, surfaces, sun;
let current = data.maps[0], quality = 'Medium', override = null, mode = 'first-person';
let attempt = createAttempt(current), view = 'driving', drivingView = '3d', map2d, zoom2d = 150;
let assignment = null, assignmentSelector, assignmentPaused = false;
const educational = () => assignment !== null;
let mapClockAt = performance.now(), mapVisible = !document.hidden && document.hasFocus(), webglFrames = 0;
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
  if(educational())return;
  closeMap();
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
  syncPresentation();
  $('view').focus({ preventScroll: true });
}
function overview() {
  if(educational())return;
  closeMap();
  pauseGame(); view = 'overview'; document.body.dataset.view = view; mode = 'overview'; controller.enabled = false; orbit.enabled = true; model.ceilings.visible = false;
  scene.fog = null;
  const w = current.driveRoad.w * CELL, h = current.driveRoad.h * CELL;
  orbit.target.set(w / 2, 0, h / 2); camera.position.set(w * 1.04, Math.max(w, h) * 0.95, h * 1.25);
  orbit.minDistance = Math.max(12, w * 0.35); orbit.maxDistance = Math.max(w, h) * 2;
  orbit.maxPolarAngle = Math.PI * 0.32; orbit.minPolarAngle = 0.12;
  orbit.enablePan = false; orbit.update(); $('camera').textContent = 'Return to driving';
  $('scene-name').textContent = 'Presentation only / 3D architecture'; metrics.reset(); syncPresentation();
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
  model = buildMazeScene(current, surfaces.materials, assignment?.questions.map(q=>q.id)); scene.add(model.group); rebuilds++;
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
  focusDriving();
}
function canDrive() { return ready && !assignmentPaused && view === 'driving' && !attempt.map.open && !attempt.interaction && !attempt.finished && !benchmarkRunning && !contextLost && !document.hidden; }
function pauseGame() { controller?.clear(); pauseAttempt(attempt); }
function settleMapTime(now = performance.now()) {
  const wasOpen = attempt.map.open;
  consumeMapAllowance(attempt, Math.max(0,now-mapClockAt), mapVisible && !assignmentPaused && !attempt.interaction && !contextLost && !benchmarkRunning);
  mapClockAt = Math.max(now,mapClockAt);
  if (wasOpen && !attempt.map.open) {
    pauseGame(); syncPresentation();
    $('status').textContent = 'Full-map allowance used · local 2D driving remains available';
  }
}
function closeMap() {
  settleMapTime(); setMapOpen(attempt,false);
}
function focusDriving() { $(view==='driving' && (drivingView==='2d' || attempt.map.open) ? 'map-view' : 'view').focus({preventScroll:true}); }
function syncPresentation() {
  const show2d = view==='driving' && (drivingView==='2d' || attempt.map.open);
  $('map-view').hidden = !show2d; $('view').hidden = show2d;
  document.body.dataset.drivingView = drivingView; document.body.dataset.mapOpen = String(attempt.map.open);
  $('map-banner').hidden = !attempt.map.open;
  $('zoom-control').hidden = !(view==='driving' && drivingView==='2d' && !attempt.map.open);
  text('toggle-view',drivingView==='3d' ? '2D driving · V' : '3D driving · V');
  $('toggle-view').setAttribute('aria-pressed',String(drivingView==='2d'));
  $('toggle-map').setAttribute('aria-pressed',String(attempt.map.open));
  if (view==='driving') {
    text('scene-name', educational() ? `${drivingView==='2d'?'2D':'3D'} assignment / ${assignment.unitId}` : drivingView==='2d' ? '2D driving / local maze' : 'Maze driving / five laboratories');
    controller.enabled = drivingView==='3d' && !attempt.map.open;
  }
  if (show2d && map2d) drawMap();
}
function drawMap() {
  const {width,height} = $('stage').getBoundingClientRect();
  map2d.render(current,attempt,{width,height,zoom:zoom2d,full:attempt.map.open});
}
function toggleDrivingView() {
  if (!ready || assignmentPaused || benchmarkRunning || view!=='driving' || attempt.interaction) return;
  closeMap(); pauseGame(); drivingView = drivingView==='3d' ? '2d' : '3d';
  syncPresentation(); refreshHud(); metrics.reset(); focusDriving();
}
function toggleMap() {
  if (!ready || assignmentPaused || benchmarkRunning || contextLost || view!=='driving' || attempt.interaction || attempt.finished) return;
  settleMapTime(); pauseGame();
  const requested = !attempt.map.open;
  if (!setMapOpen(attempt,requested) && requested) $('status').textContent = 'Full-map allowance used · local 2D driving remains available';
  syncPresentation(); refreshHud(); focusDriving();
}
function resumeDriving() {
  pauseGame(); view = 'driving'; mode = 'first-person'; document.body.dataset.view = view;
  scene.fog = new THREE.Fog('#83969b',28,85); orbit.enabled = false; controller.enabled = true; controller.driving = true;
  model.ceilings.visible = true; controller.follow(attempt.vehicle,camera);
  $('camera').textContent = '3D presentation overview'; $('inspection').value = 'driving';
  $('scene-name').textContent = 'Maze driving / five laboratories';
  syncPresentation(); metrics.reset(); refreshHud(); focusDriving();
}
function resetAttempt() {
  if (benchmarkRunning) return;
  assignmentSelector?.close();
  if(educational()){startEducationalRound(0);$('status').textContent='Fresh attempt · same unit · 25 × 19 · full map 30 s';return;}
  closeMap(); pauseGame(); attempt = createAttempt(current); mapClockAt = performance.now(); controller.pitch = 0;
  hideDialog(); resumeDriving();
  $('status').textContent = 'Attempt reset · same seed · five synthetic labs';
}
function mazeChanged(map) { return map.seed !== current.seed || map.topologyHash !== current.topologyHash || map.id !== current.id; }
function replaceMap(map, failures = 0) {
  closeMap(); pauseGame(); hideDialog();
  const changed = mazeChanged(map);
  current = map; attempt = createAttempt(current,assignment,failures); mapClockAt = performance.now(); controller.pitch = 0;
  $('maze').value=current.id;
  if (changed) rebuild();
  resumeDriving();
}
function generate() {
  if (educational() || assignmentPaused || benchmarkRunning || contextLost) return;
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
function randomSeed() { let seed=crypto.getRandomValues(new Uint32Array(1))[0];return seed===current.seed?(seed+1)>>>0:seed; }
function startEducationalRound(failures) {
  const [w,h]=attemptSize(failures),map=generateMap(w,h,randomSeed(),assignment.questions.length);
  replaceMap(map,failures);
}
function updateModeUi() {
  document.body.dataset.challenge=educational()?'education':'demo';
  text('edition',educational()?`Educational Assignment Mode · ${assignment.unitId}`:'3D Demonstration Mode');
  for(const id of ['camera','inspection','benchmark','maze','seed','generate']){
    $(id).disabled=educational();
    if(['camera','benchmark'].includes(id))$(id).hidden=educational();
    if(['inspection','maze','seed'].includes(id))$(id).closest('label').hidden=educational();
    if(id==='generate')$(id).hidden=educational();
  }
}
function setDialogInert(value) {
  for(const node of document.querySelectorAll('body > header, body > nav, body > footer, #stage > :not(#dialog-overlay)'))node.inert=value;
}
function showDialog() { $('dialog-overlay').hidden=false;setDialogInert(true);$('dialog-close').focus(); }
function hideDialog() { $('dialog-overlay').hidden=true;setDialogInert(false);$('dialog-extra').replaceChildren(); }
function refreshHud() {
  if (!model) return;
  const near = nearestInteraction(current,attempt), count = attempt.completed.filter(Boolean).length;
  text('speed',String(Math.round(Math.abs(attempt.vehicle.speed)*.25)) + (attempt.vehicle.speed<0 ? ' R' : ''));
  const total=attempt.completed.length;
  text('progress',`${count} / ${total}`);
  text('unit-status',educational()?`${assignment.unitId} · ${assignment.title} · Attempt ${attempt.failures+1} · ${current.width} × ${current.height}`:'3D Demonstration Mode · five synthetic labs');
  text('progress-label',educational()?'QUESTIONS COMPLETED':'LAB CHECKPOINTS');
  text('nearby',attempt.finished ? educational()?'Assignment complete':'Demonstration complete' : near ? `${near.id} · ${near.label}` : count===total ? 'Exit unlocked' : educational()?`Find Q01–Q0${total}`:'Find Q1–Q5');
  const active = !assignmentPaused && view==='driving' && !attempt.map.open && !benchmarkRunning;
  text('map-time',`${(attempt.map.remainingMs/1000).toFixed(1)} s remaining / 30 s`);
  text('toggle-map',`${attempt.map.open?'Close':'Full'} map · M · ${Math.ceil(attempt.map.remainingMs/1000)}s`);
  $('toggle-map').disabled = benchmarkRunning || contextLost || !!attempt.interaction || attempt.finished || (!attempt.map.open && attempt.map.remainingMs<=0) || view!=='driving';
  $('toggle-view').disabled = benchmarkRunning || !!attempt.interaction || view!=='driving';
  $('benchmark').disabled = educational() || benchmarkRunning || attempt.map.open;
  text('interaction-hint',attempt.finished ? educational()?'Reset / R or select another published unit':'Reset / R or Generate for another drive' : !active ? 'Paused · return to driving to activate' : near ? Math.abs(attempt.vehicle.speed)>25 ? 'Brake to activate · speed must be ≤25 virtual' : near.type==='finish' && count<total ? `Exit locked · complete all ${total} ${educational()?'questions':'labs'}` : 'Press E to activate' : 'W accelerate · S brake / reverse · A/D steer');
  $('interact').hidden = !active || !near || !!attempt.interaction || attempt.finished;
  model.updateProgress(attempt.completed,active ? near : null,benchmarkRunning);
  text('control-hint',testClock ? 'Test clock active · keyboard drives the real physics' : active ? 'W accelerate · S brake/reverse · A/D steer · E activate' : 'Inspection paused · drag to look · return to driving');
}
function activate() {
  if (!canDrive()) return;
  const result = interact(current,attempt);
  if (result.status==='outside') return;
  if (result.status==='moving') { $('status').textContent = 'Brake and stop near the marker before pressing E.'; focusDriving(); return; }
  if (result.status==='locked') { $('status').textContent = educational() ? 'Exit locked: answer every question correctly first.' : 'Exit locked: activate all five synthetic checkpoints first.'; focusDriving(); return; }
  if(result.status==='question'){
    const q=assignment.questions[result.index],expected=attempt,interaction=attempt.interaction;
    controller.clear();text('dialog-title',`${q.id} / ${assignment.questions.length} · ${q.title||'English question'}`);text('dialog-text',q.prompt||'Watch the English question video, then choose one answer.');
    questionContents($('dialog-extra'),assignment,q,label=>chooseAnswer(label,expected,interaction));
    text('dialog-close','Return without answering');refreshHud();showDialog();return;
  }
  if (result.status!=='activated') return;
  controller.clear(); refreshHud();
  if(educational() && result.type==='finish'){
    text('dialog-title','Assignment complete');text('dialog-text','All questions passed. Complete the published Google Form separately. No submission is recorded here.');
    finishContents($('dialog-extra'),assignment,attempt);text('dialog-close','Close completion');showDialog();return;
  }
  $('status').textContent = result.type==='finish' ? 'Demonstration complete · Reset/R or Generate for another drive' : `${result.id} activated · ${attempt.completed.filter(Boolean).length}/5 labs complete`;
  $('dialog-close').textContent = result.type==='finish' ? 'Close completion' : 'Continue driving';
  $('dialog-title').textContent = result.type==='finish' ? 'Demonstration complete' : `${result.id} · ${result.label} — Checkpoint Activated`;
  $('dialog-text').textContent = result.type==='finish' ? 'All five labs are activated. You reached the exit using the maze driving controller. No grades, student data or submission are recorded.' : 'Synthetic laboratory checkpoint activated. Continue driving to the remaining labs, then reach the unlocked exit. No course question is loaded.';
  showDialog();
}
function chooseAnswer(label,expected,interaction) {
  if(expected!==attempt || interaction!==attempt.interaction || assignmentPaused || $('dialog-overlay').hidden)return;
  const result=answerQuestion(attempt,assignment,label);
  if(result.status==='correct'){
    text('dialog-title',`Correct answer · ${assignment.questions[result.index].id} completed`);
    text('dialog-text',`${assignment.unitId} · ${assignment.title} · ${attempt.completed.filter(Boolean).length} / ${assignment.questions.length}`);
    correctContents($('dialog-extra'),assignment.questions[result.index]);text('dialog-close','Continue to the maze');refreshHud();$('dialog-close').focus();
  }else if(result.status==='wrong'){
    startEducationalRound(result.failures);attempt.interaction={type:'feedback',stage:'wrong'};
    text('dialog-title','Wrong answer · new smaller maze');text('dialog-text',`All question progress cleared. ${assignment.unitId} stays selected. Attempt ${attempt.failures+1}: ${current.width} × ${current.height}; full-map allowance restored to 30 seconds.`);
    text('dialog-close','Start the next attempt');refreshHud();showDialog();
  }
}
function closeDialog() {
  if ($('dialog-overlay').hidden) return;
  attempt.interaction = null; hideDialog(); controller.clear(); refreshHud(); focusDriving();
}
function physicsTick(dt,input) { if (canDrive()) attempt.vehicle = stepDriving(current,attempt.vehicle,input,dt); }
function advanceSimulation(seconds) {
  if (!testClock || !Number.isFinite(seconds) || seconds<0 || seconds>20) throw new Error('Only the explicit local test clock may advance 0–20 seconds');
  const input = controller.input();
  for (let remaining=seconds;remaining>1e-10;) { const dt=Math.min(1/60,remaining); physicsTick(dt,input); remaining-=dt; }
  if (view==='driving') controller.follow(attempt.vehicle,camera);
  refreshHud(); if (view==='driving' && (drivingView==='2d' || attempt.map.open)) drawMap(); return snapshot();
}
function snapshot() {
  if (!renderer) return { ready: false, webgl2: false };
  const stats = renderer.info, preset = PRESETS[quality];
  // Estimates cover owned texture mip chains and main color/depth buffers, not browser/driver overhead.
  const estimatedResources = { pbrTextureBytes: surfaces.estimatedTextureBytes,
    screenTextureBytes: (attempt.checkpoints.length+1) * 512 * 256 * 4 * 4 / 3,
    environmentApproxBytes: 2 * 1024 * 256 * 8,
    shadowApproxBytes: preset.shadow ** 2 * 4,
    framebufferApproxBytes: buffer.width * buffer.height * 8,
    note: 'Budget estimate, not measured VRAM. Excludes driver, compositor, geometry and transient allocations; shared GPU memory is not dedicated VRAM.' };
  return { phase: '3D-P2', ready, webgl2: renderer.capabilities.isWebGL2, three: THREE.REVISION,
    challengeMode:educational()?'education':'demo',assignment:assignment?{unitId:assignment.unitId,title:assignment.title,schemaVersion:assignment.schemaVersion,questionCount:assignment.questions.length}:null,assignmentPaused,
    baseline: data.baseline, generatorHash: data.generatorHash, quality, scaleOverride: override,
    targetFps: Number($('fps').value), buffer, devicePixelRatio: window.devicePixelRatio, rendererPixelRatio: renderer.getPixelRatio(),
    viewport: { width: innerWidth, height: innerHeight }, mode, view, drivingView, navigationView: view==='driving' ? `driving${drivingView}` : view,
    zoom2d, map2d: map2d?.snapshot(), webglFrames, testClock, game: JSON.parse(JSON.stringify(attempt)), heldKeys: [...controller.keys], metersPerSecond: virtualSpeedToMeters(attempt.vehicle.speed), vehicleClear: canDriveStand(current,attempt.vehicle.x,attempt.vehicle.y), pose: { ...controller.pose },
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
  delete report.map2d;
  delete report.assignment;
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
  if (educational() || assignmentPaused || !ready || benchmarkRunning || contextLost || attempt.interaction || attempt.map.open) return;
  warmupMs = Math.max(200, Math.min(10000, warmupMs)); durationMs = Math.max(600, Math.min(60000, durationMs));
  pauseGame();
  const saved = { current, attempt, view, drivingView, inspection: $('inspection').value, pose: { ...controller.pose } };
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
      const result = snapshot(); delete result.benchmarkResults; delete result.game; delete result.heldKeys; delete result.map2d; delete result.assignment;
      benchmarkResults.push({ scenario: name, warmupMs, durationMs, report: result });
    }
  } finally {
    const changed = mazeChanged(saved.current);
    benchmark = null; benchmarkRunning = false; current = saved.current; attempt = saved.attempt; drivingView = saved.drivingView; mapClockAt = performance.now(); $('maze').value = current.id;
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
  settleMapTime(now);
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
  if (view==='driving' && (drivingView==='2d' || attempt.map.open)) {
    drawMap();
    if (now-lastPanel>750) { $('fps-badge').textContent='2D active'; $('stats').textContent=`Canvas 2D active · WebGL retained, rendering paused\n${map2d.builds} static cache builds\n${display(map2d.snapshot().cpuPaintMeanMs)} ms mean Canvas paint\nFull map ${(attempt.map.remainingMs/1000).toFixed(1)} / 30 s`; lastPanel=now; }
    return;
  }
  metrics.begin(now); renderer.render(scene, camera); metrics.end(); webglFrames++;
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
  map2d = new Map2D($('map-view'));
  metrics = new Metrics(renderer); controller = new Controller(canvas, { reset: resetAttempt, pause: pauseGame, close: () => assignmentSelector?.dialog.open ? assignmentSelector.close() : attempt.map.open ? toggleMap() : closeDialog(), interact: activate, canDrive, toggleView:toggleDrivingView, toggleMap });
  orbit = new OrbitControls(camera, canvas); orbit.enabled = false; orbit.enableDamping = true;
  rebuild(); resumeDriving(); cold.sceneBuiltMs = performance.now();
  cold.initialPreset = quality; cold.initialMaze = current.id; cold.initialBuffer = { ...buffer };
  const prep = performance.now(); await renderer.compileAsync(scene, camera);
  cold.shaderPreparationMs = performance.now() - prep; cold.readyMs = performance.now();
  ready = true; mapVisible = !document.hidden && document.hasFocus(); mapClockAt = performance.now(); message('');
  assignmentSelector=new AssignmentSelector({
    canOpen:()=>ready&&!benchmarkRunning&&!contextLost&&!attempt.interaction,
    pause:()=>{settleMapTime();assignmentPaused=true;pauseGame();},
    resume:()=>{assignmentPaused=false;mapClockAt=performance.now();refreshHud();focusDriving();},
    unit:unit=>{assignment=unit;updateModeUi();startEducationalRound(0);},
    demo:()=>{assignment=null;updateModeUi();replaceMap(generateMap(25,19,randomSeed()));}
  });
  updateModeUi();
  const networkNotice=()=>{$('offline-note').hidden=navigator.onLine;};
  window.addEventListener('online',networkNotice);window.addEventListener('offline',networkNotice);networkNotice();
  $('dialog-overlay').addEventListener('keydown',event=>{
    if(event.key!=='Tab')return;
    const nodes=[...$('dialog-overlay').querySelectorAll('button,a[href]')].filter(n=>!n.disabled);
    const index=nodes.indexOf(document.activeElement),next=event.shiftKey?(index-1+nodes.length)%nodes.length:(index+1)%nodes.length;
    event.preventDefault();nodes[next]?.focus();
  });
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
  $('toggle-view').addEventListener('click',toggleDrivingView); $('toggle-map').addEventListener('click',toggleMap); $('close-map').addEventListener('click',toggleMap);
  $('zoom2d').addEventListener('change',() => { zoom2d=Number($('zoom2d').value); syncPresentation(); focusDriving(); });
  $('map-view').addEventListener('pointerdown',focusDriving);
  $('interact').addEventListener('click',activate); $('dialog-close').addEventListener('click',closeDialog);
  $('camera').addEventListener('click', () => view==='driving' ? overview() : resumeDriving());
  $('fullscreen').addEventListener('click', async () => {
    try { if (document.fullscreenElement) await document.exitFullscreen(); else await document.documentElement.requestFullscreen(); }
    catch { $('status').textContent = 'Fullscreen unavailable. Use the browser fullscreen command (F11 on Windows).'; }
    focusDriving();
  });
  $('benchmark').addEventListener('click', () => runBenchmark());
  $('cancel-benchmark').addEventListener('click', () => { cancelBenchmark = true; });
  $('export').addEventListener('click', exportResults);
  new ResizeObserver(resize).observe($('stage')); window.addEventListener('resize', resize);
  const visibility = () => { settleMapTime(); mapVisible = !document.hidden && document.hasFocus(); metrics.reset(); lastFrame = performance.now(); };
  document.addEventListener('visibilitychange',visibility); window.addEventListener('focus',visibility); window.addEventListener('blur',visibility);
  window.showcase = Object.freeze({ snapshot, runBenchmark, ...(testClock ? { advanceSimulation } : {}) });
  window.addEventListener('pagehide', () => { cancelBenchmark = true; metrics.dispose(); model.dispose(); surfaces.dispose(); environment.dispose(); orbit.dispose(); renderer.dispose(); });
  requestAnimationFrame(frame);
}
initialize().catch(error => {
  message(error.message || 'The local 3D scene could not initialize. Reload or use the Lite edition.', true);
  $('status').textContent = '3D unavailable · no course data has been loaded';
  document.querySelectorAll('button, select').forEach(el => { el.disabled = true; });
});
