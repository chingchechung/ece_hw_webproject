import * as THREE from 'three';
import { CELL, HEIGHT, rectangles, wallRuns, road, center, terminalPose, DIRECTIONS } from '../maze/layout.js';

function quads() {
  const positions = [], normals = [], uvs = [], indices = [];
  return {
    add(points, normal, coordinates) {
      const offset = positions.length / 3;
      points.forEach((p, i) => { positions.push(...p); normals.push(...normal); uvs.push(...coordinates[i]); });
      indices.push(offset, offset + 1, offset + 2, offset, offset + 2, offset + 3);
    },
    finish() {
      const g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
      g.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
      g.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
      g.setIndex(indices); g.computeBoundingSphere(); return g;
    }
  };
}
export function horizontalGeometry(rects, y, reversed = false) {
  const q = quads();
  rects.forEach(r => {
    const x = r.x * CELL, z = r.z * CELL, x2 = (r.x + r.w) * CELL, z2 = (r.z + r.d) * CELL;
    const points = [[x, y, z], [x, y, z2], [x2, y, z2], [x2, y, z]];
    if (reversed) points.reverse();
    q.add(points, [0, reversed ? -1 : 1, 0], points.map(p => [p[0] / 2.8, p[2] / 2.8]));
  });
  return q.finish();
}
export function wallsGeometry(runs, low = 0, high = HEIGHT, inset = 0) {
  const q = quads();
  runs.forEach(r => {
    const [dx, dz] = DIRECTIONS[r.direction], fixed = r.fixed * CELL;
    const a = r.start * CELL, b = r.end * CELL;
    let points = r.direction % 2 === 0
      ? [[fixed - dx * inset, low, a], [fixed - dx * inset, high, a], [fixed - dx * inset, high, b], [fixed - dx * inset, low, b]]
      : [[a, low, fixed - dz * inset], [b, low, fixed - dz * inset], [b, high, fixed - dz * inset], [a, high, fixed - dz * inset]];
    if (r.direction === 0 || r.direction === 1) points.reverse();
    q.add(points, [-dx, 0, -dz], points.map(p => [(r.direction % 2 === 0 ? p[2] : p[0]) / 2.8, p[1] / HEIGHT]));
  });
  return q.finish();
}
function contactGeometry(runs) {
  const q = quads();
  runs.forEach(r => {
    const [dx, dz] = DIRECTIONS[r.direction], f = r.fixed * CELL, a = r.start * CELL, b = r.end * CELL;
    const point = (along, inset) => r.direction % 2 === 0 ? [f - dx * inset, 0.004, along] : [along, 0.004, f - dz * inset];
    q.add([point(a, 0.01), point(b, 0.01), point(b, 0.24), point(a, 0.24)], [0, 1, 0], [[0, 0], [1, 0], [1, 1], [0, 1]]);
  });
  const geometry = q.finish(), colors = [];
  runs.forEach(() => colors.push(0.53, 0.61, 0.64, 0.53, 0.61, 0.64, 1, 1, 1, 1, 1, 1));
  geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
  return geometry;
}
function instances(geometry, material, transforms, parent, name) {
  const mesh = new THREE.InstancedMesh(geometry, material, transforms.length);
  const dummy = new THREE.Object3D();
  transforms.forEach((t, i) => {
    dummy.position.set(t.x, t.y, t.z); dummy.rotation.set(0, t.yaw || 0, 0);
    dummy.scale.set(t.sx || 1, t.sy || 1, t.sz || 1); dummy.updateMatrix(); mesh.setMatrixAt(i, dummy.matrix);
  });
  mesh.name = name; mesh.castShadow = true; mesh.receiveShadow = true; parent.add(mesh); return mesh;
}
function paintScreen(c, label, exit = false, state = '') {
  const g = c.getContext('2d');
  g.fillStyle = '#0c2732'; g.fillRect(0, 0, 512, 256);
  g.fillStyle = state === 'COMPLETE' || state === 'UNLOCKED' ? '#b3e2c3' : state ? '#eed297' : exit ? '#b3e2c3' : '#87d3cd';
  g.font = 'bold 52px monospace'; g.fillText(label, 24, 62);
  g.font = '19px monospace'; g.fillText(state || (exit ? 'DEMONSTRATION / EXIT' : 'SIGNAL ANALYSIS / DEMO'), 24, 94);
  g.strokeStyle = '#22434a'; g.lineWidth = 1;
  for (let x = 24; x < 490; x += 32) { g.beginPath(); g.moveTo(x, 112); g.lineTo(x, 230); g.stroke(); }
  for (let y = 112; y < 240; y += 24) { g.beginPath(); g.moveTo(24, y); g.lineTo(490, y); g.stroke(); }
  g.strokeStyle = exit ? '#b2dfae' : '#dbd5a0'; g.lineWidth = 3; g.beginPath();
  for (let x = 24; x < 490; x++) g.lineTo(x, 173 + Math.sin(x * 0.04) * 39);
  g.stroke();
}
function screenTexture(label, exit = false) {
  const c = Object.assign(document.createElement('canvas'), { width: 512, height: 256 });
  paintScreen(c, label, exit);
  const texture = new THREE.CanvasTexture(c); texture.colorSpace = THREE.SRGBColorSpace; return texture;
}
export function buildMazeScene(map, materials, checkpointLabels = null) {
  const group = new THREE.Group(), ceilings = new THREE.Group(), extras = [];
  const screenResources = [];
  group.name = 'deterministic-maze'; group.add(ceilings);
  const runs = wallRuns(map), floors = rectangles(map), solids = rectangles(map, false);
  const add = (geometry, material, name, parent = group) => {
    const mesh = new THREE.Mesh(geometry, material); mesh.name = name; mesh.receiveShadow = true;
    mesh.castShadow = name === 'walls'; parent.add(mesh); return mesh;
  };
  add(horizontalGeometry(floors, 0), materials.floor, 'road-floor');
  add(wallsGeometry(runs), materials.wall, 'walls');
  add(horizontalGeometry(solids, HEIGHT), materials.top, 'wall-caps');
  add(horizontalGeometry(floors, HEIGHT + 0.22, true), materials.ceiling, 'ceiling', ceilings);
  // Real inset skirting and crown bands; separate depth avoids coplanar fighting.
  add(wallsGeometry(runs, 0.02, 0.18, 0.012), materials.dark, 'skirting');
  add(wallsGeometry(runs, HEIGHT - 0.18, HEIGHT - 0.08, 0.016), materials.accent, 'crown');
  add(wallsGeometry(runs, 0.20, 0.225, 0.018), materials.gold, 'safety-line');
  const contactMaterial = new THREE.MeshBasicMaterial({ vertexColors: true, blending: THREE.MultiplyBlending,
    transparent: true, premultipliedAlpha: true, toneMapped: false, depthWrite: false, side: THREE.DoubleSide });
  extras.push(contactMaterial);
  add(contactGeometry(runs), contactMaterial, 'baked-contact').renderOrder = 1;
  const seams = [];
  runs.forEach(r => {
    const [dx, dz] = DIRECTIONS[r.direction];
    for (let along = Math.ceil(r.start * CELL / 2.8) * 2.8; along < r.end * CELL; along += 2.8) {
      seams.push({ x: r.direction % 2 === 0 ? r.fixed * CELL - dx * 0.018 : along,
        z: r.direction % 2 === 0 ? along : r.fixed * CELL - dz * 0.018,
        y: HEIGHT / 2, yaw: r.direction % 2 === 0 ? Math.PI / 2 : 0 });
    }
  });
  instances(new THREE.BoxGeometry(0.025, HEIGHT - 0.4, 0.038), materials.dark, seams, group, 'recessed-panel-joints');
  const base = add(new THREE.BoxGeometry(map.driveRoad.w * CELL, 0.3, map.driveRoad.h * CELL), materials.dark, 'plinth');
  base.position.set(map.driveRoad.w * CELL / 2, -0.18, map.driveRoad.h * CELL / 2);
  const housings = [], strips = [], dashes = [];
  for (let y = 1; y < map.height - 1; y += 2) for (let x = 1; x < map.width - 1; x += 2) {
    if (map.grid[y * 2][x * 2]) continue;
    const p = center({ x, y });
    housings.push({ ...p, y: HEIGHT + 0.03 }); strips.push({ ...p, y: HEIGHT - 0.05 });
    DIRECTIONS.slice(0, 2).forEach(([dx, dz]) => {
      if (map.grid[(y + dz) * 2][(x + dx) * 2] !== 0) return;
      dashes.push({ x: p.x + dx * 1.4, z: p.z + dz * 1.4, y: 0.006, yaw: dz ? 0 : Math.PI / 2 });
    });
  }
  instances(new THREE.BoxGeometry(1.9, 0.10, 0.45), materials.dark, housings, ceilings, 'light-housings');
  instances(new THREE.BoxGeometry(1.7, 0.035, 0.29), materials.light, strips, ceilings, 'ceiling-panels');
  instances(new THREE.BoxGeometry(0.045, 0.008, 0.65), materials.gold, dashes, group, 'route-stitches');
  // Synthetic demo instruments: five repeated solid pedestal parts, unique local screens.
  const terminals = map.stations.map(p => terminalPose(map, p));
  instances(new THREE.BoxGeometry(1.15, 0.12, 0.8), materials.dark, terminals.map(t => ({ ...t, y: 0.06 })), group, 'terminal-bases');
  instances(new THREE.BoxGeometry(0.43, 0.9, 0.43), materials.dark, terminals.map(t => ({ ...t, y: 0.55 })), group, 'terminal-stems');
  instances(new THREE.BoxGeometry(1.18, 0.86, 0.28), materials.top, terminals.map(t => ({ ...t, y: 1.45 })), group, 'oscilloscope-bodies');
  terminals.forEach((t, i) => {
    const texture = screenTexture(checkpointLabels?.[i] ?? `LAB ${String(i + 1).padStart(2, '0')}`);
    const material = new THREE.MeshStandardMaterial({ map: texture, emissiveMap: texture, emissive: '#ffffff', emissiveIntensity: 0.55, roughness: 0.5 });
    extras.push(texture, material);
    screenResources.push({ texture, material });
    const screen = add(new THREE.PlaneGeometry(1.02, 0.64), material, 'instrument-screen');
    screen.position.set(t.x + Math.sin(t.yaw) * 0.147, 1.47, t.z + Math.cos(t.yaw) * 0.147); screen.rotation.y = t.yaw;
  });
  const exit = center(map.exit), pose = DIRECTIONS.find(([dx, dz]) => road(map,
    Math.floor((exit.x + dx * 3.5) / CELL), Math.floor((exit.z + dz * 3.5) / CELL))) || [1, 0];
  const yaw = Math.atan2(pose[0], pose[1]), exitGroup = new THREE.Group();
  exitGroup.position.set(exit.x, 0, exit.z); exitGroup.rotation.y = yaw; group.add(exitGroup);
  const posts = [-1.65, 1.65].map(x => ({ x, y: 1.45, z: 0 }));
  instances(new THREE.BoxGeometry(0.22, 2.9, 0.36), materials.accent, posts, exitGroup, 'exit-posts');
  const beam = add(new THREE.BoxGeometry(3.55, 0.65, 0.4), materials.exit, 'exit-beam', exitGroup); beam.position.y = 2.85;
  const texture = screenTexture('EXIT  →', true), material = new THREE.MeshStandardMaterial({ map: texture, emissiveMap: texture, emissive: '#ffffff', emissiveIntensity: 0.5 });
  extras.push(texture, material);
  const sign = add(new THREE.PlaneGeometry(2.4, 0.5), material, 'exit-sign', exitGroup); sign.position.set(0, 2.86, 0.205);
  let progressKey = '';
  return { group, ceilings, stats: { wallRuns: runs.length, floorRectangles: floors.length,
    openCells: map.driveRoad.bits.filter(Boolean).length },
    setMaterials(next) {
      group.traverse(object => {
        for (const key of Object.keys(materials)) if (object.material === materials[key]) { object.material = next[key]; break; }
      });
      materials = next; progressKey = '';
    },
    updateProgress(completed, nearby = null, presentation = false) {
      const key = completed.join(',') + ':' + (nearby?.id || '') + ':' + presentation;
      if (key === progressKey) return; progressKey = key;
      screenResources.forEach((r,i) => {
        const state = presentation ? '' : completed[i] ? 'COMPLETE' : nearby?.index === i ? 'READY / PRESS E WHEN STOPPED' : checkpointLabels ? 'ENGLISH QUESTION / PRESS E' : 'SIGNAL ANALYSIS / DEMO';
        paintScreen(r.texture.image, checkpointLabels?.[i] ?? `LAB ${String(i+1).padStart(2,'0')}`, false, state);
        r.texture.needsUpdate = true;
        r.material.emissiveIntensity = presentation ? .55 : completed[i] ? .8 : nearby?.index === i ? .95 : .55;
      });
      const unlocked = completed.every(Boolean);
      paintScreen(texture.image, 'EXIT  →', true, presentation ? '' : unlocked ? 'UNLOCKED' : `LOCKED / COMPLETE ALL ${completed.length} ${checkpointLabels?'QUESTIONS':'LABS'}`);
      texture.needsUpdate = true;
      beam.material.color.set(presentation ? '#aac3b3' : unlocked ? '#a4dfb8' : '#c4b596');
      beam.material.emissive.set(presentation ? '#35775d' : unlocked ? '#438d64' : '#4c3c21');
    },
    dispose() {
      group.traverse(object => { if (object.geometry) object.geometry.dispose(); if (object.isInstancedMesh) object.dispose(); });
      extras.forEach(resource => resource.dispose()); group.removeFromParent();
    } };
}
