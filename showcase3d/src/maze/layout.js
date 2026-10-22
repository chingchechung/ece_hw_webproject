export const CELL = 0.7;
export const HEIGHT = 3.6;
export const DIRECTIONS = [[1, 0], [0, 1], [-1, 0], [0, -1]];
export const center = p => ({ x: (4 * p.x + 2) * CELL, z: (4 * p.y + 2) * CELL });
export function road(map, x, z) {
  const { w, h, bits } = map.driveRoad;
  return x >= 0 && z >= 0 && x < w && z < h && bits[z * w + x] === 1;
}
export function walkable(map, x, z, radius = 0.25) {
  for (let i = 0; i < 9; i++) {
    const a = i * Math.PI / 4;
    const r = i === 8 ? 0 : radius;
    if (!road(map, Math.floor((x + Math.cos(a) * r) / CELL),
      Math.floor((z + Math.sin(a) * r) / CELL))) return false;
  }
  return true;
}
export function terminalPose(map, point) {
  const c = center(point);
  const direction = DIRECTIONS.find(([dx, dz]) => !road(map,
    Math.floor((c.x + dx * 2.5) / CELL), Math.floor((c.z + dz * 2.5) / CELL))) || [0, -1];
  const [dx, dz] = direction;
  return { x: c.x + dx * 1.25, z: c.z + dz * 1.25, y: 0, yaw: Math.atan2(-dx, -dz), dx, dz };
}
// One maximal rectangle per row-run, then extend equal runs vertically.
export function rectangles(map, open = true) {
  const { w, h } = map.driveRoad, result = [], active = new Map();
  for (let z = 0; z < h; z++) {
    const next = new Map();
    for (let x = 0; x < w;) {
      if (road(map, x, z) !== open) { x++; continue; }
      const start = x;
      while (x < w && road(map, x, z) === open) x++;
      const key = `${start}:${x}`;
      const existing = active.get(key);
      if (existing) { existing.d++; next.set(key, existing); }
      else { const item = { x: start, z, w: x - start, d: 1 }; result.push(item); next.set(key, item); }
    }
    active.clear();
    for (const [key, value] of next) active.set(key, value);
  }
  return result;
}
// Merge only collinear, identically oriented exposed solid/road boundaries.
// These very edges also define floor coverage and contact trim: no invented doors.
export function wallRuns(map) {
  const groups = new Map(), { w, h } = map.driveRoad;
  for (let z = 0; z < h; z++) for (let x = 0; x < w; x++) {
    if (!road(map, x, z)) continue;
    DIRECTIONS.forEach(([dx, dz], direction) => {
      if (road(map, x + dx, z + dz)) return;
      const fixed = direction % 2 === 0 ? x + (dx === 1 ? 1 : 0) : z + (dz === 1 ? 1 : 0);
      const along = direction % 2 === 0 ? z : x;
      const key = `${direction}:${fixed}`;
      if (!groups.has(key)) groups.set(key, { direction, fixed, cells: [] });
      groups.get(key).cells.push(along);
    });
  }
  const runs = [];
  for (const { direction, fixed, cells } of groups.values()) {
    cells.sort((a, b) => a - b);
    for (let i = 0; i < cells.length;) {
      const start = cells[i]; let end = start + 1; i++;
      while (i < cells.length && cells[i] === end) { end++; i++; }
      runs.push({ direction, fixed, start, end });
    }
  }
  return runs;
}
export function junctions(map) {
  const result = [];
  for (let y = 1; y < map.height - 1; y++) for (let x = 1; x < map.width - 1; x++) {
    if (map.grid[y * 2][x * 2] !== 0) continue;
    const exits = DIRECTIONS.map(([dx, dz]) => map.grid[(y + dz) * 2][(x + dx) * 2] === 0);
    result.push({ x, y, exits, degree: exits.filter(Boolean).length });
  }
  return result;
}
export function viewPose(map, type = 'start') {
  if (type === 'checkpoint') {
    const c = center(map.stations[0]), t = terminalPose(map, map.stations[0]);
    const x = c.x - t.dx * 1.4 - t.dz * 1.1, z = c.z - t.dz * 1.4 + t.dx * 1.1;
    return { x, z, yaw: Math.atan2(t.z - z, t.x - x), pitch: -0.04 };
  }
  if (type === 'checkpoint' || type === 'finish') {
    const point = center(type === 'finish' ? map.exit : map.stations[0]);
    const approach = DIRECTIONS.find(([dx, dz]) => walkable(map, point.x + dx * 3.5, point.z + dz * 3.5));
    const [dx, dz] = approach || [1, 0];
    return { x: point.x + dx * 3.2, z: point.z + dz * 3.2, yaw: Math.atan2(-dz, -dx), pitch: -0.02 };
  }
  const points = junctions(map);
  const degree = type === 'four-way' ? 4 : type === 't-junction' ? 3 : 2;
  const selected = type === 'start' ? points.find(p => p.x === 1 && p.y === 1)
    : points.find(p => p.degree === degree && (degree !== 2 || (p.exits[0] && p.exits[2]) || (p.exits[1] && p.exits[3])));
  const point = selected || points[0];
  const direction = point.exits.findIndex(Boolean), [dx, dz] = DIRECTIONS[direction];
  const p = center(point);
  // Look into a junction from its actual incoming corridor.
  const offset = ['four-way', 't-junction'].includes(type) ? 2.6 : 0;
  return { x: p.x + dx * offset, z: p.z + dz * offset,
    yaw: Math.atan2(offset ? -dz : dz, offset ? -dx : dx), pitch: 0 };
}
export function move(map, pose, distance) {
  const steps = Math.max(1, Math.ceil(Math.abs(distance) / 0.08));
  for (let i = 0; i < steps; i++) {
    const dx = Math.cos(pose.yaw) * distance / steps, dz = Math.sin(pose.yaw) * distance / steps;
    if (walkable(map, pose.x + dx, pose.z)) pose.x += dx;
    if (walkable(map, pose.x, pose.z + dz)) pose.z += dz;
  }
}
