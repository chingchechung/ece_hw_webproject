import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { exportMaps, sha256, baseline } from '../scripts/export-maze.mjs';
import { CELL, HEIGHT, road, walkable, rectangles, wallRuns, viewPose, move, junctions, DIRECTIONS } from '../src/maze/layout.js';
import { wallsGeometry, horizontalGeometry } from '../src/scene/geometry.js';
import { PRESETS, resolution, summarize } from '../src/performance/quality.js';

const data = exportMaps();
test('read-only adapter is pinned to the reviewed generator and deterministic', () => {
  assert.equal(data.baseline, baseline);
  assert.equal(data.generatorHash, '03cd7fe5e60aec7d9cb47a799a8facfd73e4e3137602f5fd4edadb73b34ea564');
  assert.deepEqual(data, exportMaps());
  assert.deepEqual(data, JSON.parse(readFileSync(new URL('../src/maze/maps.json', import.meta.url))));
});
test('69 approved Lite implementation/test/contract files remain byte-identical', () => {
  const manifest = JSON.parse(readFileSync(new URL('lite-baseline.json', import.meta.url)));
  assert.equal(Object.keys(manifest).length, 69);
  for (const [path, hash] of Object.entries(manifest)) assert.equal(sha256(readFileSync(new URL(`../../${path}`, import.meta.url))), hash, path);
});
function winding(geometry) {
  const p = geometry.attributes.position.array, n = geometry.attributes.normal.array, idx = geometry.index.array;
  for (let i = 0; i < idx.length; i += 3) {
    const [a, b, c] = Array.from(idx.slice(i, i + 3), j => j * 3);
    const ab = [p[b] - p[a], p[b + 1] - p[a + 1], p[b + 2] - p[a + 2]];
    const ac = [p[c] - p[a], p[c + 1] - p[a + 1], p[c + 2] - p[a + 2]];
    const cross = [ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2], ab[0] * ac[1] - ab[1] * ac[0]];
    assert.ok(cross.reduce((sum, v, j) => sum + v * n[a + j], 0) > 0);
  }
  assert.ok([...p, ...geometry.attributes.uv.array].every(Number.isFinite));
  geometry.dispose();
}
for (const map of data.maps) {
  test(`${map.id}: continuous floors cover every road cell exactly once, no solid cells`, () => {
    const { w, h } = map.driveRoad, coverage = new Uint8Array(w * h);
    rectangles(map).forEach(r => {
      for (let z = r.z; z < r.z + r.d; z++) for (let x = r.x; x < r.x + r.w; x++) coverage[z * w + x]++;
    });
    assert.deepEqual(Array.from(coverage), map.driveRoad.bits);
    winding(horizontalGeometry(rectangles(map), 0));
    winding(horizontalGeometry(rectangles(map, false), HEIGHT));
  });
  test(`${map.id}: every solid/road boundary has exactly one wall, no false openings`, () => {
    const actual = new Set();
    wallRuns(map).forEach(r => { for (let a = r.start; a < r.end; a++) {
      const key = `${r.direction}:${r.fixed}:${a}`; assert.ok(!actual.has(key)); actual.add(key);
    } });
    const expected = new Set(), { w, h } = map.driveRoad;
    for (let z = 0; z < h; z++) for (let x = 0; x < w; x++) if (road(map, x, z)) {
      DIRECTIONS.forEach(([dx, dz], d) => {
        if (!road(map, x + dx, z + dz)) expected.add(`${d}:${d % 2 === 0 ? x + (dx === 1 ? 1 : 0) : z + (dz === 1 ? 1 : 0)}:${d % 2 === 0 ? z : x}`);
      });
    }
    assert.deepEqual(actual, expected); winding(wallsGeometry(wallRuns(map)));
  });
  test(`${map.id}: connected looped mask, genuine T/four-way junctions and safe poses`, () => {
    const { w, h } = map.driveRoad, visited = new Set(), queue = [map.driveRoad.bits.findIndex(Boolean)];
    for (let i = 0; i < queue.length; i++) {
      const p = queue[i]; if (visited.has(p)) continue; visited.add(p);
      const x = p % w, z = Math.floor(p / w);
      DIRECTIONS.forEach(([dx, dz]) => { const n = (z + dz) * w + x + dx;
        if (road(map, x + dx, z + dz) && !visited.has(n)) queue.push(n); });
    }
    assert.equal(visited.size, map.driveRoad.bits.filter(Boolean).length);
    assert.ok(junctions(map).some(p => p.degree === 3));
    // At least one loop in logical graph: E >= V, distinct from widened-cell loops.
    const nodes = junctions(map); assert.ok(nodes.reduce((a, p) => a + p.degree, 0) / 2 >= nodes.length);
    for (const type of ['start', 'straight', 't-junction', 'four-way', 'checkpoint', 'finish']) {
      const pose = viewPose(map, type); assert.ok(walkable(map, pose.x, pose.z), `${type}: ${JSON.stringify(pose)}`);
    }
    assert.equal(map.stations.length, 5); assert.ok(w > h);
  });
  test(`${map.id}: swept prototype movement never tunnels through walls`, () => {
    const pose = viewPose(map);
    for (let i = 0; i < 200; i++) { pose.yaw += 0.17; move(map, pose, i % 2 ? 0.7 : -0.3); assert.ok(walkable(map, pose.x, pose.z)); }
    move(map, pose, 200); assert.ok(walkable(map, pose.x, pose.z));
    assert.ok(!walkable(map, -1, -1)); assert.ok(!walkable(map, 0, 0));
  });
}
test('full-size deterministic map contains the promised four-way inspection junction', () => {
  assert.ok(junctions(data.maps[0]).some(p => p.degree === 4));
});
test('DPR-independent bounded framebuffers, all presets and laptop/projector layouts', () => {
  for (const preset of Object.keys(PRESETS)) for (const [w, h] of [[1280, 800], [1920, 1080], [3840, 2160]]) {
    for (const override of [null, 0.5, 0.7, 0.85, 1, 1.25]) {
      const r = resolution(w, h, preset, override);
      assert.ok(r.width <= PRESETS[preset].width && r.height <= PRESETS[preset].height);
      assert.ok(Math.abs(r.width / r.height - w / h) < 0.01);
    }
  }
  assert.deepEqual(resolution(1280, 800, 'Low'), { width: 896, height: 560, scale: 0.7 });
});
test('mean/p95 handle empty, singleton and tail outliers without fabricated values', () => {
  assert.deepEqual(summarize([]), { mean: null, p95: null });
  assert.deepEqual(summarize([33]), { mean: 33, p95: 33 });
  assert.equal(summarize([...Array(18).fill(10), 100, 200]).p95, 100);
});
