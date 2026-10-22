// Controlled adaptation of lite-v1.0 game.js; parity-tested against its actual functions.
// Pure data in/out, no DOM or Three.js. Units: Lite world pixels and virtual speed.
import { LITE_ROAD_TILE, VIRTUAL_DISTANCE_FACTOR, logicalToLite } from './coordinates.js';
export const TOP_SPEED = 590;
export const MAX_FRAME_DT = 0.045; // Same cap as Lite's frame(), including long stalls.
export function driveRoadAt(map, x, y) {
  const { w, h, bits } = map.driveRoad, gx = Math.floor(x / LITE_ROAD_TILE), gy = Math.floor(y / LITE_ROAD_TILE);
  return gx >= 0 && gy >= 0 && gx < w && gy < h && bits[gy * w + gx] === 1;
}
export function canDriveStand(map, x, y) {
  const r = 6;
  return driveRoadAt(map, x, y) && driveRoadAt(map, x-r, y-r) && driveRoadAt(map, x+r, y-r)
    && driveRoadAt(map, x-r, y+r) && driveRoadAt(map, x+r, y+r) && driveRoadAt(map, x-r, y)
    && driveRoadAt(map, x+r, y) && driveRoadAt(map, x, y-r) && driveRoadAt(map, x, y+r);
}
export function rayDistance(map, ox, oy, angle, maxDist) {
  const road = map.driveRoad, unit = LITE_ROAD_TILE, ux = Math.cos(angle), uy = Math.sin(angle), gx = ox/unit, gy = oy/unit;
  let cx = Math.floor(gx), cy = Math.floor(gy);
  const sx = ux < 0 ? -1 : 1, sy = uy < 0 ? -1 : 1;
  const dx = Math.abs(ux) < 1e-8 ? 1e30 : Math.abs(1/ux), dy = Math.abs(uy) < 1e-8 ? 1e30 : Math.abs(1/uy);
  let nextX = ux < 0 ? (gx-cx)*dx : (cx+1-gx)*dx, nextY = uy < 0 ? (gy-cy)*dy : (cy+1-gy)*dy, dist = 0;
  for (let i = 0; i < road.w + road.h + 6 && dist < maxDist; i++) {
    if (nextX < nextY) { dist = nextX*unit; nextX += dx; cx += sx; }
    else { dist = nextY*unit; nextY += dy; cy += sy; }
    if (cx < 0 || cy < 0 || cx >= road.w || cy >= road.h || !road.bits[cy*road.w+cx]) break;
  }
  return Math.min(dist, maxDist);
}
export function chooseDriveHeading(map, x, y, preferred = Math.PI/2) {
  let bestAngle = preferred, bestDist = -1;
  [0, Math.PI/2, Math.PI, -Math.PI/2].forEach(a => {
    const d = rayDistance(map, x, y, a, 300);
    if (d > bestDist) { bestDist = d; bestAngle = a; }
  });
  return rayDistance(map, x, y, preferred, 300) < 75 ? bestAngle : preferred;
}
export function initialVehicle(map) {
  const p = logicalToLite({ x: 1, y: 1 });
  return { ...p, heading: chooseDriveHeading(map, p.x, p.y), speed: 0, distance: 0, walk: 0, moving: false, steer: 0 };
}
export function stepDriving(map, vehicle, input, elapsed) {
  const dt = Math.max(0, Math.min(MAX_FRAME_DT, Number.isFinite(elapsed) ? elapsed : 0));
  if (!dt) return { ...vehicle };
  const v = { ...vehicle }, gas = !!(input.w || input.arrowup), brake = !!(input.s || input.arrowdown);
  const left = !!(input.a || input.arrowleft), right = !!(input.d || input.arrowright);
  if (gas) v.speed += 320*dt;
  if (brake) v.speed -= 620*dt;
  if (!gas && !brake) v.speed *= Math.exp(-1.35*dt);
  v.speed = Math.max(-135, Math.min(v.speed, TOP_SPEED));
  if (Math.abs(v.speed) < 1.4) v.speed = 0;
  v.steer = (right ? 1 : 0) - (left ? 1 : 0);
  const speedNorm = Math.abs(v.speed)/TOP_SPEED;
  if (v.steer) v.heading += v.steer*(2.8-1.0*speedNorm)*dt*(v.speed < -5 ? -1 : 1);
  const step = v.speed*dt/VIRTUAL_DISTANCE_FACTOR, dx = Math.cos(v.heading)*step, dy = Math.sin(v.heading)*step;
  let moved = 0;
  if (canDriveStand(map, v.x+dx, v.y+dy)) { v.x += dx; v.y += dy; moved = Math.hypot(dx, dy); }
  else {
    let mx = false, my = false;
    if (canDriveStand(map, v.x+dx, v.y)) { v.x += dx; mx = true; }
    if (canDriveStand(map, v.x, v.y+dy)) { v.y += dy; my = true; }
    if (mx || my) { moved = Math.hypot(mx ? dx : 0, my ? dy : 0); v.speed *= .65; }
    else v.speed = 0;
  }
  v.distance += moved*VIRTUAL_DISTANCE_FACTOR;
  v.moving = Math.abs(v.speed) > 8;
  v.walk += dt*Math.abs(v.speed)/VIRTUAL_DISTANCE_FACTOR/16;
  return v;
}
